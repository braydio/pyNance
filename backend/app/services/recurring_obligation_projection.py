"""Project recurring cash obligations into the Safe-to-Spend protection horizon.

``project_cash_obligations`` is pure and deterministic: callers pass plain dataclasses (no database
session, clock or network) and an explicit ``as_of``. It expands confirmed streams and qualifying
high-confidence provisional candidates with ``forecast.v2_core.expand_scheduled_events`` (the single
calendar implementation), merges them with planned bills and returns each occurrence exactly once.

Amounts are positive cents of cash leaving a checking/savings account. Candidates stay
``proposed`` in storage; a provisional reserve is a temporary safety margin the user can reject.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from math import ceil
from typing import Any, Optional

from forecast.v2_core import ForecastV2InputError, expand_scheduled_events

PROVISIONAL_MIN_CYCLES = 3
PROVISIONAL_MIN_CONFIDENCE = 0.85
DEDUPE_WINDOW_DAYS = 3
PAID_MATCH_WINDOW_DAYS = 3
FIXED_PAID_TOLERANCE_CENTS = 100
FIXED_PAID_TOLERANCE_RATIO = 0.05
# A candidate whose newest evidence is older than this many cadence periods is stale.
STALE_PERIODS = 2
CADENCE_DAYS = {
    "weekly": 7,
    "biweekly": 14,
    "semimonthly": 16,
    "monthly": 31,
    "quarterly": 92,
    "yearly": 366,
}
SOURCE_RANK = {"planned_bill": 0, "recurring_confirmed": 1, "recurring_provisional": 2}


@dataclass(frozen=True)
class StreamInput:
    """One owner-verified recurring stream, already narrowed to a cash-leaving account."""

    stream_id: str
    account_id: str
    name: str
    merchant_key: str
    amount_cents: int  # positive cash outflow per occurrence
    amount_mode: str  # fixed | variable
    cadence: str
    anchor_date: date
    status: str  # confirmed | proposed
    source: str  # manual | detected | legacy
    confidence: Optional[float] = None
    evidence_cycles: int = 0
    evidence_amounts_cents: tuple[int, ...] = ()
    last_observed: Optional[date] = None
    eligible: bool = True  # False when role/account makes it a non-debit (own transfer, card purchase)
    ineligible_reason: Optional[str] = None


@dataclass(frozen=True)
class PlannedBillInput:
    """A manual planned bill from the baseline scenario."""

    bill_id: str
    name: str
    account_id: Optional[str]
    due_date: date
    amount_cents: int
    source_stream_id: Optional[str] = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PostedOutflow:
    """A posted cash debit, used only to recognise that an occurrence was already paid."""

    account_id: str
    day: date
    amount_cents: int


def _name_key(value: str) -> str:
    return " ".join(str(value or "").lower().split())[:160]


def _quantize_cents(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def conservative_estimate_cents(stream: StreamInput) -> tuple[int, Optional[int], Optional[int], bool]:
    """Return ``(amount, low, high, estimated)`` for one occurrence.

    Fixed streams and manual variable streams use the persisted amount. A detected variable stream
    uses the upper quartile of its non-outlier posted evidence (never below the persisted amount).
    """
    if stream.amount_mode != "variable" or stream.source == "manual":
        return stream.amount_cents, None, None, False
    values = sorted(a for a in stream.evidence_amounts_cents if a > 0)
    if len(values) < PROVISIONAL_MIN_CYCLES:
        return stream.amount_cents, None, None, True
    median = values[len(values) // 2]
    kept = [v for v in values if median / 2 <= v <= median * 2] or values
    upper = kept[max(ceil(0.75 * len(kept)) - 1, 0)]
    return max(upper, stream.amount_cents), min(kept), max(kept), True


def _is_stale(stream: StreamInput, as_of: date) -> bool:
    if stream.last_observed is None:
        return True
    period = CADENCE_DAYS.get(stream.cadence, 31)
    return (as_of - stream.last_observed).days > period * STALE_PERIODS


def _classify_stream(stream: StreamInput, as_of: date) -> tuple[Optional[str], Optional[str]]:
    """Return ``(tier, reason)``; tier is ``confirmed``/``provisional``/``needs_review``/``None``."""
    if not stream.eligible:
        return None, stream.ineligible_reason or "not_cash_debit"
    if stream.amount_cents <= 0:
        return None, "ambiguous_sign"
    if stream.status == "confirmed":
        return "confirmed", None
    if stream.status != "proposed" or stream.source != "detected":
        return None, "inactive"
    if stream.evidence_cycles < PROVISIONAL_MIN_CYCLES:
        return "needs_review", "needs_review_insufficient_cycles"
    if (stream.confidence or 0.0) < PROVISIONAL_MIN_CONFIDENCE:
        return "needs_review", "needs_review_low_confidence"
    if _is_stale(stream, as_of):
        return "needs_review", "stale_evidence"
    return "provisional", None


def _expand(stream: StreamInput, amount_cents: int, start: date, end: date) -> list[date]:
    spec: dict[str, Any] = {
        "source_id": stream.stream_id,
        "kind": "scheduled_bill",
        "amount": -Decimal(amount_cents) / 100,  # scheduled_bill amounts are signed cash deltas
        "account_id": stream.account_id,
        "cadence": stream.cadence,
        "anchor_date": stream.anchor_date,
    }
    if stream.cadence == "semimonthly":
        other = stream.anchor_date.day + 15 if stream.anchor_date.day <= 15 else stream.anchor_date.day - 15
        spec["days"] = sorted({stream.anchor_date.day, other})
    return [event.date for event in expand_scheduled_events([spec], start, end)]


def _already_paid(
    stream_account: str,
    amount_cents: int,
    mode: str,
    due: date,
    as_of: date,
    posted: list[PostedOutflow],
    used: set[int],
) -> bool:
    """Match one unconsumed posted debit near ``due`` so a paid bill is not reserved twice."""
    if due > as_of:
        return False
    for index, item in enumerate(posted):
        if index in used or item.account_id != stream_account:
            continue
        if abs((item.day - due).days) > PAID_MATCH_WINDOW_DAYS:
            continue
        if mode == "variable":
            ok = amount_cents * 0.5 <= item.amount_cents <= amount_cents * 1.5
        else:
            tolerance = max(FIXED_PAID_TOLERANCE_CENTS, int(amount_cents * FIXED_PAID_TOLERANCE_RATIO))
            ok = abs(item.amount_cents - amount_cents) <= tolerance
        if ok:
            used.add(index)
            return True
    return False


def _row(
    *,
    row_id: str,
    name: str,
    account_id: Optional[str],
    due: date,
    amount: int,
    source: str,
    status: str,
    estimated: bool,
    reasons: list[str],
    key: tuple,
    display_end: date,
    extra: Optional[dict] = None,
) -> dict[str, Any]:
    return {
        "id": row_id,
        "name": name,
        "account_id": account_id,
        "due_date": due.isoformat(),
        "amount_cents": amount,
        "source": source,
        "status": status,
        "estimated": estimated,
        "reason_codes": reasons,
        "in_display_window": due <= display_end,
        "_key": key,
        **(extra or {}),
    }


def project_cash_obligations(
    streams: Iterable[StreamInput],
    planned_bills: Iterable[PlannedBillInput],
    posted_outflows: Iterable[PostedOutflow],
    as_of: date,
    protection_end: date,
    display_end: Optional[date] = None,
) -> dict[str, Any]:
    """Return merged, de-duplicated obligations in inclusive ``[as_of, protection_end]``.

    Result keys: ``rows`` (reserved), ``needs_review`` (informational), ``skipped`` (reason codes per
    source) and ``totals`` (``planned``, ``confirmed``, ``provisional``, ``needs_review``,
    ``display_due`` and ``protection_reserved`` cents).
    """
    display_end = display_end or as_of
    posted = list(posted_outflows)
    used_posted: set[int] = set()
    rows: list[dict[str, Any]] = []
    review: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []

    for bill in sorted(planned_bills, key=lambda b: (b.due_date, b.bill_id)):
        if not as_of <= bill.due_date <= protection_end or bill.amount_cents <= 0:
            continue
        rows.append(
            _row(
                row_id=bill.bill_id,
                name=bill.name,
                account_id=bill.account_id,
                due=bill.due_date,
                amount=bill.amount_cents,
                source="planned_bill",
                status="planned",
                estimated=False,
                reasons=["planned_bill"],
                key=(bill.account_id, bill.source_stream_id or bill.bill_id, bill.due_date),
                display_end=display_end,
                extra={"_stream_id": bill.source_stream_id, "_name_key": _name_key(bill.name), **bill.extra},
            )
        )

    for stream in sorted(streams, key=lambda s: (s.anchor_date, s.stream_id)):
        tier, reason = _classify_stream(stream, as_of)
        if tier is None:
            skipped.append({"source_id": stream.stream_id, "reason": reason or "inactive"})
            continue
        amount, low, high, estimated = conservative_estimate_cents(stream)
        try:
            due_dates = _expand(stream, amount, as_of, protection_end)
        except ForecastV2InputError:
            skipped.append({"source_id": stream.stream_id, "reason": "unknown_phase"})
            continue
        for due in due_dates:
            if _already_paid(stream.account_id, amount, stream.amount_mode, due, as_of, posted, used_posted):
                skipped.append({"source_id": stream.stream_id, "reason": "already_paid", "due_date": due.isoformat()})
                continue
            reasons = [f"cadence_{stream.cadence}"]
            if tier == "confirmed":
                reasons.insert(0, "confirmed_stream")
            elif tier == "provisional":
                reasons.insert(0, "provisional_high_confidence")
            else:
                reasons.insert(0, reason or "needs_review")
            if estimated:
                reasons.append("estimated_amount")
            extra = {"_stream_id": stream.stream_id, "_name_key": _name_key(stream.name)}
            if low is not None:
                extra["amount_range_cents"] = {"min": low, "max": high}
            row = _row(
                row_id=stream.stream_id,
                name=stream.name,
                account_id=stream.account_id,
                due=due,
                amount=amount,
                source="recurring_confirmed" if tier == "confirmed" else "recurring_provisional",
                status=tier,
                estimated=estimated,
                reasons=reasons,
                key=(stream.account_id, stream.stream_id, due),
                display_end=display_end,
                extra=extra,
            )
            (review if tier == "needs_review" else rows).append(row)

    rows = _dedupe(rows)
    rows.sort(key=lambda r: (r["due_date"], r["name"], r["id"]))
    review.sort(key=lambda r: (r["due_date"], r["name"], r["id"]))
    totals = {
        "planned": sum(r["amount_cents"] for r in rows if r["status"] == "planned"),
        "confirmed": sum(r["amount_cents"] for r in rows if r["status"] == "confirmed"),
        "provisional": sum(r["amount_cents"] for r in rows if r["status"] == "provisional"),
        "needs_review": sum(r["amount_cents"] for r in review),
    }
    totals["protection_reserved"] = totals["planned"] + totals["confirmed"] + totals["provisional"]
    totals["display_due"] = sum(r["amount_cents"] for r in rows if r["in_display_window"])
    return {"rows": _public(rows), "needs_review": _public(review), "skipped": skipped, "totals": totals}


def _dedupe(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep one row per stable key, then drop recurring rows a planned bill already covers.

    Precedence is planned bill > confirmed stream > provisional. A lower-ranked row is suppressed
    only for the same account when a shared source id matches, or when exactly one higher-ranked
    row has the same name, the same amount and a due date within three days (so distinct
    same-merchant tiers or a second valid plan stay).
    """
    by_key: dict[tuple, dict[str, Any]] = {}
    for row in sorted(rows, key=lambda r: (SOURCE_RANK[r["source"]], r["due_date"], r["id"])):
        by_key.setdefault(row["_key"], row)
    ordered = sorted(by_key.values(), key=lambda r: (SOURCE_RANK[r["source"]], r["due_date"], r["id"]))
    kept: list[dict[str, Any]] = []
    for row in ordered:
        if row["source"] != "planned_bill" and _covered(row, kept):
            continue
        kept.append(row)
    return kept


def _covered(row: dict[str, Any], kept: list[dict[str, Any]]) -> bool:
    higher = [
        k
        for k in kept
        if SOURCE_RANK[k["source"]] < SOURCE_RANK[row["source"]] and k["account_id"] == row["account_id"]
    ]
    for other in higher:
        if other.get("_stream_id") and other["_stream_id"] == row["_stream_id"] and other["_key"][2] == row["_key"][2]:
            return True
    matches = [
        other
        for other in higher
        if other["_name_key"] == row["_name_key"]
        and other["amount_cents"] == row["amount_cents"]
        and abs((date.fromisoformat(other["due_date"]) - date.fromisoformat(row["due_date"])).days)
        <= DEDUPE_WINDOW_DAYS
    ]
    return len(matches) == 1


def _public(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{k: v for k, v in row.items() if not k.startswith("_")} for row in rows]


def history_coverage(earliest_tx: Optional[date], as_of: date, min_days: int = 90) -> list[str]:
    """Coverage warning codes from how much posted history exists for the cash accounts."""
    if earliest_tx is None:
        return ["no_transactions"]
    if (as_of - earliest_tx).days < min_days:
        return ["partial_history"]
    return []


__all__ = [
    "PlannedBillInput",
    "PostedOutflow",
    "StreamInput",
    "conservative_estimate_cents",
    "history_coverage",
    "project_cash_obligations",
]

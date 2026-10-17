"""Reproducible next-payday inference from posted cash income.

The detector is pure: it receives already-classified posted income events and a fixed ``as_of`` date,
so results are deterministic and testable with synthetic dates. It never treats an unverified guess as
confirmed, never merges unrelated payers into one cadence, and returns *no* date when the evidence is
thin (fewer than ``MIN_CYCLES`` distinct pay dates for one payer).

Precedence: user schedule > confirmed owned income stream > inferred payroll-like stream > unresolved.
"""

from __future__ import annotations

import calendar
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from statistics import median
from typing import Any, Iterable, Mapping, Optional, Sequence

MIN_CYCLES = 3
STALE_SYNC_DAYS = 7
CENT = Decimal("0.01")
CADENCES = ("weekly", "biweekly", "semimonthly", "monthly")
_PERIOD_DAYS = {"weekly": 7, "biweekly": 14, "semimonthly": 15, "monthly": 30}
_NOISE = re.compile(r"\b(ppd|ach|id|co|direct|dep|deposit|payroll|pmt|credit|web|ccd|corp|inc|llc)\b|[^a-z ]")


@dataclass(frozen=True)
class PayEvent:
    """One posted, visible, owner-confirmed cash inflow considered as a possible paycheck."""

    day: date
    amount: Decimal
    payer_key: str
    account_id: str = ""


def payer_key_for(*texts: Optional[str]) -> str:
    """Stable grouping key for one payer: lowercase letters with banking noise words removed."""
    for text in texts:
        cleaned = " ".join(_NOISE.sub(" ", str(text or "").lower()).split())
        if cleaned and cleaned != "unknown":
            return cleaned[:40]
    return "unknown payer"


def payer_label_for(payer_key: str) -> str:
    """Redacted display label: only the first word of the payer, never the raw memo."""
    word = (payer_key.split() or ["payer"])[0]
    return word[:16].title()


def _cents(value: Decimal) -> int:
    return int((value.quantize(CENT) * 100).to_integral_value())


def _last_day(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def _month_add(day: date, months: int, target_day: int) -> date:
    index = day.year * 12 + (day.month - 1) + months
    year, month = divmod(index, 12)
    month += 1
    return date(year, month, min(target_day, _last_day(year, month)))


def _is_month_end(day: date) -> bool:
    return day.day >= _last_day(day.year, day.month) - 2 or day.day <= 2


def _is_mid(day: date) -> bool:
    return 13 <= day.day <= 17


def _detect_cadence(days: Sequence[date]) -> tuple[Optional[str], list[str]]:
    """Return ``(cadence, reasons)`` for sorted distinct pay dates (``None`` when irregular)."""
    gaps = [(b - a).days for a, b in zip(days, days[1:])]
    if all(6 <= g <= 8 for g in gaps):
        return "weekly", []
    # Semi-monthly: dates alternate between the mid-month and the month-end/start clusters.
    if all(_is_mid(d) or _is_month_end(d) for d in days):
        kinds = [_is_mid(d) for d in days]
        if all(a != b for a, b in zip(kinds, kinds[1:])) and all(9 <= g <= 19 for g in gaps):
            if len(days) >= 4:
                return "semimonthly", []
            # Three alternating dates fit both semimonthly and a drifting biweekly: refuse to guess.
            return None, ["ambiguous_cadence"]
    if all(12 <= g <= 16 or 26 <= g <= 30 for g in gaps) and any(12 <= g <= 16 for g in gaps):
        return "biweekly", ["skipped_cycle"] if any(g >= 26 for g in gaps) else []
    day_numbers = [d.day for d in days]
    if all(26 <= g <= 35 for g in gaps):
        spread = max(day_numbers) - min(day_numbers)
        month_end = all(_is_month_end(d) for d in days)
        if spread <= 3 or month_end:
            return "monthly", []
    return None, ["irregular_cadence"]


def _next_after(cadence: str, days: Sequence[date], as_of: date) -> Optional[date]:
    """First expected pay date on/after ``as_of`` strictly later than the last observed pay date."""
    last = days[-1]
    floor = max(as_of, last + timedelta(days=1))
    if cadence in {"weekly", "biweekly"}:
        step = timedelta(days=_PERIOD_DAYS[cadence])
        candidate = last + step
        while candidate < floor:
            candidate += step
        return candidate
    if cadence == "monthly":
        target = int(median([d.day for d in days]))
        if all(_is_month_end(d) and d.day > 2 for d in days):
            target = 31
        candidate = _month_add(last, 1, target)
        while candidate < floor:
            candidate = _month_add(candidate, 1, target)
        return candidate
    # semimonthly: the mid-month day seen (median) and the month end.
    mid = int(median([d.day for d in days if _is_mid(d)]))
    start_of_month = [d for d in days if d.day <= 2]
    candidates: list[date] = []
    cursor = date(floor.year, floor.month, 1)
    for _ in range(3):
        candidates.append(date(cursor.year, cursor.month, min(mid, _last_day(cursor.year, cursor.month))))
        if start_of_month and len(start_of_month) * 2 >= len([d for d in days if not _is_mid(d)]):
            candidates.append(date(cursor.year, cursor.month, 1))
        else:
            candidates.append(date(cursor.year, cursor.month, _last_day(cursor.year, cursor.month)))
        cursor = _month_add(cursor, 1, 1)
    return min(c for c in candidates if c >= floor and c > last)


def _unresolved(as_of: date, reasons: list[str]) -> dict[str, Any]:
    return {
        "next_payday": None,
        "confidence": "none",
        "source": "unresolved",
        "source_label": "No validated payday",
        "amount_cents": None,
        "cadence": None,
        "observed_dates": [],
        "observed_amount_cents": [],
        "history_start": None,
        "history_end": None,
        "reason_codes": reasons,
        "needs_review": True,
        "as_of": as_of.isoformat(),
        "candidates": [],
    }


def _infer_group(events: list[PayEvent], as_of: date) -> Optional[dict[str, Any]]:
    by_day: dict[date, Decimal] = {}
    for event in events:
        by_day[event.day] = by_day.get(event.day, Decimal("0")) + event.amount
    days = sorted(by_day)
    if len(days) < MIN_CYCLES:
        return None
    cadence, reasons = _detect_cadence(days)
    if cadence is None:
        return None
    amounts = [by_day[d] for d in days]
    mid_amount = Decimal(str(median(amounts))).quantize(CENT)
    variable = mid_amount > 0 and any(abs(a - mid_amount) / mid_amount > Decimal("0.3") for a in amounts)
    # The last cycle must be recent: more than ~two periods of silence means the stream stopped or sync is stale.
    if (as_of - days[-1]).days > 2 * _PERIOD_DAYS[cadence] + 3:
        return None
    next_day = _next_after(cadence, days, as_of)
    if next_day is None:
        return None
    confidence = "medium" if len(days) >= 4 and not reasons and not variable else "low"
    reasons = list(reasons) + ["variable_amount"] * variable + [f"cycles_{len(days)}"]
    return {
        "next_payday": next_day,
        "confidence": confidence,
        "source": "inferred_stream",
        "source_label": "Inferred from posted deposits",
        "amount_cents": None if variable else _cents(mid_amount),
        "cadence": cadence,
        "observed_dates": [d.isoformat() for d in days],
        "observed_amount_cents": [_cents(a) for a in amounts],
        "history_start": days[0].isoformat(),
        "history_end": days[-1].isoformat(),
        "reason_codes": reasons,
        "needs_review": True,
        "payer_label": payer_label_for(events[0].payer_key),
    }


def _confirmed_candidate(stream: Mapping[str, Any], as_of: date, source: str, label: str) -> Optional[dict[str, Any]]:
    next_day = stream.get("next_due")
    if not isinstance(next_day, date):
        return None
    amount = stream.get("amount")
    return {
        "next_payday": next_day,
        "confidence": "high",
        "source": source,
        "source_label": label,
        "amount_cents": _cents(Decimal(str(amount))) if amount is not None else None,
        "cadence": stream.get("cadence"),
        "observed_dates": [],
        "observed_amount_cents": [],
        "history_start": None,
        "history_end": None,
        "reason_codes": [source],
        "needs_review": False,
        "payer_label": payer_label_for(payer_key_for(stream.get("name"))),
    }


def _public(candidate: dict[str, Any]) -> dict[str, Any]:
    out = dict(candidate)
    if isinstance(out.get("next_payday"), date):
        out["next_payday"] = out["next_payday"].isoformat()
    return out


def infer_payday(
    posted_events: Iterable[PayEvent],
    as_of: date,
    confirmed_streams: Sequence[Mapping[str, Any]] = (),
    user_schedule: Optional[Mapping[str, Any]] = None,
    *,
    data_through: Optional[date] = None,
) -> dict[str, Any]:
    """Return the deterministic next-payday prediction and every candidate that supports it.

    Args:
        posted_events: Posted, visible, owner cash inflows already classified as wage-like income.
            Events after ``as_of`` are ignored.
        as_of: Fixed evaluation date.
        confirmed_streams: Owner-confirmed income streams as ``{name, amount, cadence, next_due}``
            where ``next_due`` is a ``date``.
        user_schedule: Optional explicit ``{name, amount, cadence, next_due}`` that outranks everything.
        data_through: Newest posted activity date of any kind; older than a week marks stale sync.

    Returns:
        ``{next_payday, confidence, source, source_label, amount_cents, cadence, observed_dates,
        observed_amount_cents, history_start, history_end, reason_codes, needs_review, candidates}``.
        ``next_payday`` is an ISO date or ``None`` when nothing meets the evidence threshold.
    """
    candidates: list[dict[str, Any]] = []
    if user_schedule:
        candidate = _confirmed_candidate(user_schedule, as_of, "user_schedule", "Your pay schedule")
        if candidate:
            candidates.append(candidate)
    for stream in confirmed_streams:
        candidate = _confirmed_candidate(stream, as_of, "confirmed_stream", "Confirmed income stream")
        if candidate:
            candidates.append(candidate)

    groups: dict[str, list[PayEvent]] = defaultdict(list)
    seen = 0
    for event in posted_events:
        if event.day <= as_of and event.amount > 0:
            groups[event.payer_key].append(event)
            seen += 1
    inferred = [c for c in (_infer_group(g, as_of) for _, g in sorted(groups.items())) if c]
    candidates.extend(inferred)
    stale = data_through is not None and (as_of - data_through).days > STALE_SYNC_DAYS

    eligible = [c for c in candidates if c["next_payday"] >= as_of]
    if not eligible:
        reasons = ["insufficient_history"] if seen < MIN_CYCLES else ["no_regular_payer"]
        if stale:
            reasons.append("stale_sync")
        return _unresolved(as_of, reasons)

    rank = {"user_schedule": 0, "confirmed_stream": 1, "inferred_stream": 2}
    eligible.sort(key=lambda c: (rank[c["source"]], c["next_payday"], c.get("payer_label", "")))
    best = dict(eligible[0])
    # Within the winning tier prefer the nearest date (the sort above already orders by date).
    if stale:
        best["reason_codes"] = best["reason_codes"] + ["stale_sync"]
        best["needs_review"] = True
    if len({c["payer_label"] for c in inferred}) > 1:
        best["reason_codes"] = best["reason_codes"] + ["multiple_payers"]
    best["as_of"] = as_of.isoformat()
    best["candidates"] = [_public({k: v for k, v in c.items() if k != "candidates"}) for c in eligible]
    return _public(best)

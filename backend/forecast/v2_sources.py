"""Forecast V2 sources: turn transaction history into scheduled events plus a residual model.

Pure and deterministic (no DB, clock or network). It produces the inputs for
``forecast.v2_core.simulate_cash_ledger`` and an audit proving every in-scope transaction was
used exactly once, so promoted recurring cashflows (paychecks, rent, subscriptions) are never
double counted inside the variable-spending average.

Sign convention for input transactions: ``amount`` is the signed effect on the transaction's own
account as stored by pyNance (positive = money in, negative = money out). Liability-account
purchases are negative; payments received by a card are positive.

Buckets (each in-scope transaction lands in exactly one):
    scheduled     allocated to a promoted recurring stream (manual rule, saved rule or inferred)
    residual      ordinary variable spending/income, fed to the weekday residual model
    transfer      paired/internal movement between the user's own accounts, never spending
    duplicate     repeated transaction id
    pending       not posted yet (superseded by a booked row or simply not final)
    unclassified  cannot be used (non-cash/non-debt account type, malformed amount, ...)

Liability policy: credit-account purchases are treated as cash-spend proxies in the residual
model, and the cash-to-card payment that settles them is a ``transfer`` (liquidity effect
modeled through the purchases), so household spending is not counted twice.
"""

from __future__ import annotations

import hashlib
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from datetime import date, timedelta
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any, Optional

from .models import ForecastV2Event
from .v2_core import (
    BUCKET_CASH,
    BUCKET_LIABILITY,
    CENT,
    ForecastV2InputError,
    _clamp_day,
    _read,
    _to_date,
    _to_decimal,
    classify_forecast_account,
    expand_scheduled_events,
)

DEFAULT_OPTIONS: dict[str, Any] = {
    "lookback_days": 120,
    "amount_tolerance": 0.15,
    "min_occurrences": 3,
    "promote_threshold": 0.6,
    "min_history_days": 14,
    "min_weekday_samples": 4,
    "winsor_percentile": 0.05,
    "pending_match_days": 7,
}
ZERO = Decimal("0.00")
_SUPPORTED_FREQUENCIES = {
    "weekly": "weekly",
    "biweekly": "biweekly",
    "bi-weekly": "biweekly",
    "every_two_weeks": "biweekly",
    "semimonthly": "semimonthly",
    "monthly": "monthly",
    "once": "once",
}


# --------------------------------------------------------------------------- helpers


def normalize_merchant_key(transaction: Any) -> str:
    """Stable merchant identity: ``merchant_slug`` else normalized name/description."""
    slug = _read(transaction, "merchant_slug")
    if slug:
        return str(slug).strip().lower()
    text = _read(transaction, "merchant_name") or _read(transaction, "name") or _read(transaction, "description")
    text = re.sub(r"[0-9#*]+", " ", str(text or "").lower())
    text = re.sub(r"[^a-z ]+", " ", text)
    return " ".join(text.split()) or "unknown"


def _stream_id(account_id: str, merchant_key: str, sign: int, cluster: int) -> str:
    raw = f"{account_id}|{merchant_key}|{sign}|{cluster}"
    return "stream:" + hashlib.sha1(raw.encode()).hexdigest()[:12]


def _median(values: Sequence[Decimal]) -> Decimal:
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return ((ordered[mid - 1] + ordered[mid]) / 2).quantize(CENT, rounding=ROUND_HALF_EVEN)


def _level(confidence: float) -> str:
    return "high" if confidence >= 0.8 else "medium" if confidence >= 0.6 else "low"


def _month_len_anchor(year: int, month: int, day: int) -> date:
    return _clamp_day(year, month, day)


def _near_monthly_anchor(day: date, mode_day: int) -> int:
    """Smallest day distance from ``day`` to the (clamped) ``mode_day`` of a nearby month."""
    best = 99
    for offset in (-1, 0, 1):
        month = day.month + offset
        year = day.year + (month - 1) // 12
        month = (month - 1) % 12 + 1
        best = min(best, abs((day - _month_len_anchor(year, month, mode_day)).days))
    return best


# --------------------------------------------------------------------------- scope & buckets


def _entry(tx: Any, bucket: str, reason: str, **extra: Any) -> dict[str, Any]:
    amount = _read(tx, "_amount")
    return {
        "transaction_id": str(_read(tx, "transaction_id")),
        "account_id": str(_read(tx, "account_id")),
        "date": _read(tx, "_date").isoformat(),
        "amount": f"{amount:.2f}",
        "bucket": bucket,
        "reason": reason,
        **extra,
    }


def _prepare(transactions: Iterable[Any], accounts: Mapping[str, str], as_of: date, window_start: date):
    """Return ``(usable, rejected_counts)`` with parsed ``_date``/``_amount`` fields attached."""
    usable: list[dict[str, Any]] = []
    rejected = {"foreign_account": 0, "after_as_of": 0, "before_window": 0, "malformed": 0}
    for tx in transactions:
        account_id = _read(tx, "account_id")
        if account_id is None or str(account_id) not in accounts:
            rejected["foreign_account"] += 1  # never trust a caller-supplied account list
            continue
        try:
            day = _to_date(_read(tx, "date"))
            amount = _to_decimal(_read(tx, "amount"))
        except ForecastV2InputError:
            rejected["malformed"] += 1
            continue
        if day > as_of:
            rejected["after_as_of"] += 1
            continue
        if day < window_start:
            rejected["before_window"] += 1
            continue
        record = dict(tx) if isinstance(tx, Mapping) else dict(vars(tx))
        record.update(
            account_id=str(account_id),
            transaction_id=str(_read(tx, "transaction_id")),
            _date=day,
            _amount=amount,
            _merchant=normalize_merchant_key(tx),
        )
        usable.append(record)
    usable.sort(key=lambda r: (r["_date"], r["transaction_id"]))
    return usable, rejected


def _classify_basic(usable: list[dict[str, Any]], accounts: Mapping[str, str], opts: Mapping[str, Any]):
    """First pass: duplicates, pending, transfers, unusable account types.

    Returns ``(audit_by_id, candidates)`` where candidates continue to recurrence/residual.
    """
    audit: dict[str, dict[str, Any]] = {}
    seen: set[str] = set()
    posted = [t for t in usable if not t.get("pending")]
    by_id = {t["transaction_id"]: t for t in usable}
    candidates: list[dict[str, Any]] = []

    def booked_equivalent(pending: dict[str, Any]) -> bool:
        link = pending.get("pending_transaction_id")
        if link and any(t.get("pending_transaction_id") == pending["transaction_id"] for t in posted):
            return True
        window = timedelta(days=int(opts["pending_match_days"]))
        return any(
            p["account_id"] == pending["account_id"]
            and p["_amount"] == pending["_amount"]
            and p["_merchant"] == pending["_merchant"]
            and pending["_date"] <= p["_date"] <= pending["_date"] + window
            for p in posted
        )

    for tx in usable:
        txid = tx["transaction_id"]
        if txid in seen:
            audit.setdefault(("dup", txid, len(audit)), _entry(tx, "duplicate", "repeated_transaction_id"))
            continue
        seen.add(txid)
        if tx.get("pending"):
            audit[txid] = _entry(
                tx, "pending", "booked_equivalent_exists" if booked_equivalent(tx) else "not_posted_yet"
            )
            continue
        account_bucket = accounts[tx["account_id"]]
        if account_bucket not in (BUCKET_CASH, BUCKET_LIABILITY):
            audit[txid] = _entry(tx, "unclassified", "non_cash_account")
            continue
        if tx.get("is_internal") or tx.get("internal_match_id") or tx.get("transfer_type"):
            counterpart = by_id.get(str(tx.get("internal_match_id"))) if tx.get("internal_match_id") else None
            kind = "unmatched"
            if counterpart is not None:
                other = accounts.get(counterpart["account_id"])
                kind = (
                    "cash_to_cash"
                    if other == account_bucket == BUCKET_CASH
                    else ("liability_payment" if BUCKET_LIABILITY in (other, account_bucket) else "cross_account")
                )
            audit[txid] = _entry(tx, "transfer", "internal_transfer", transfer_kind=kind)
            continue
        candidates.append(tx)
    return audit, candidates


# --------------------------------------------------------------------------- recurrence


def _detect_cadence(dates: Sequence[date]) -> Optional[dict[str, Any]]:
    """Classify the cadence of a sorted list of distinct dates, or ``None`` if irregular."""
    if len(dates) < 2:
        return None
    gaps = [(b - a).days for a, b in zip(dates, dates[1:])]

    def share(lo: int, hi: int) -> float:
        return sum(lo <= g <= hi for g in gaps) / len(gaps)

    if share(6, 8) >= 0.8:
        return {"cadence": "weekly", "fit": share(6, 8)}
    if share(13, 15) >= 0.8:
        return {"cadence": "biweekly", "fit": share(13, 15)}
    if share(27, 34) >= 0.8:
        doms = Counter(d.day for d in dates)
        mode_day = sorted(doms.items(), key=lambda kv: (-kv[1], -kv[0]))[0][0]
        fit = sum(_near_monthly_anchor(d, mode_day) <= 3 for d in dates) / len(dates)
        if fit >= 0.75:
            return {"cadence": "monthly", "fit": min(fit, share(27, 34)), "day": mode_day}
        return None
    if len(dates) >= 4 and share(12, 18) >= 0.8:
        days = sorted(d.day for d in dates)
        widest = max(range(len(days) - 1), key=lambda i: days[i + 1] - days[i])
        low, high = days[: widest + 1], days[widest + 1 :]
        if (
            len(low) >= 2
            and len(high) >= 2
            and high[0] - low[-1] >= 8
            and max(low) - min(low) <= 4
            and max(high) - min(high) <= 4
        ):
            first = Counter(low).most_common(1)[0][0]
            second = Counter(high).most_common(1)[0][0]
            return {"cadence": "semimonthly", "fit": share(12, 18), "days": [first, second]}
    return None


def _cluster_amounts(items: list[dict[str, Any]], tolerance: float) -> list[list[dict[str, Any]]]:
    """Split one merchant's transactions into amount clusters (separate subscriptions)."""
    clusters: list[list[dict[str, Any]]] = []
    for item in sorted(items, key=lambda t: (abs(t["_amount"]), t["_date"], t["transaction_id"])):
        magnitude = abs(item["_amount"])
        for cluster in clusters:
            anchor = abs(cluster[0]["_amount"])
            if magnitude <= anchor * (Decimal(1) + Decimal(str(tolerance))):
                cluster.append(item)
                break
        else:
            clusters.append([item])
    return clusters


def _monthly_anchor(last_seen: date, mode_day: int) -> date:
    """A date carrying ``mode_day`` on or before ``last_seen`` (so no occurrence is skipped)."""
    year, month = last_seen.year, last_seen.month
    for _ in range(12):
        try:
            candidate = date(year, month, mode_day)
        except ValueError:
            month -= 1
            if month == 0:
                year, month = year - 1, 12
            continue
        return candidate
    return last_seen


def _infer_streams(candidates: list[dict[str, Any]], as_of: date, opts: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Group candidates into streams and detect cadence/amount for each."""
    groups: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for tx in candidates:
        if tx["_amount"] != 0:
            groups[(tx["account_id"], tx["_merchant"], 1 if tx["_amount"] > 0 else -1)].append(tx)
    streams: list[dict[str, Any]] = []
    for (account_id, merchant, sign), items in sorted(groups.items()):
        for cluster_index, cluster in enumerate(_cluster_amounts(items, float(opts["amount_tolerance"]))):
            dates = sorted({t["_date"] for t in cluster})
            detected = _detect_cadence(dates) if len(dates) >= 2 else None
            amounts = [t["_amount"] for t in cluster]
            median = _median(amounts)
            stream: dict[str, Any] = {
                "stream_id": _stream_id(account_id, merchant, sign, cluster_index),
                "origin": "inferred",
                "account_id": account_id,
                "merchant_key": merchant,
                "sign": sign,
                "amount": median,
                "transactions": cluster,
                "dates": dates,
                "last_seen": dates[-1],
                "cadence": None,
                "confidence": 0.0,
                "reason": "",
            }
            if detected is None or len(dates) < 2:
                stream["reason"] = "no_regular_cadence" if len(dates) > 1 else "single_occurrence"
            else:
                n = len(dates)
                evidence = min(0.95, 0.55 + 0.1 * (n - 2))
                stream.update(
                    cadence=detected["cadence"],
                    confidence=round(min(0.95, evidence * detected["fit"]), 2),
                    days=detected.get("days"),
                    day=detected.get("day"),
                )
                stream["reason"] = f"{n}_occurrences"
            streams.append(stream)
    return streams


def _next_anchor(stream: Mapping[str, Any]) -> date:
    """Anchor date from which ``expand_scheduled_events`` reproduces the cadence."""
    last: date = stream["last_seen"]
    cadence = stream["cadence"]
    if cadence in {"weekly", "biweekly"}:
        return last
    if cadence == "monthly":
        return _monthly_anchor(last, stream.get("day") or last.day)
    return last - timedelta(days=45)  # semimonthly rules carry explicit days


def _lapsed(stream: Mapping[str, Any], as_of: date) -> bool:
    gap = {"weekly": 7, "biweekly": 14, "semimonthly": 16, "monthly": 31}.get(stream["cadence"])
    return gap is not None and (as_of - stream["last_seen"]).days > gap * 2.5


# --------------------------------------------------------------------------- residual model


def _percentile(values: Sequence[Decimal], q: float) -> Decimal:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round(q * (len(ordered) - 1)))))
    return ordered[index]


def _winsorized_mean(values: Sequence[Decimal], q: float) -> Decimal:
    if not values:
        return ZERO
    low, high = _percentile(values, q), _percentile(values, 1 - q)
    clipped = [min(max(v, low), high) for v in values]
    return (sum(clipped, ZERO) / len(clipped)).quantize(CENT, rounding=ROUND_HALF_EVEN)


def _residual_model(
    residual: list[dict[str, Any]], grid_start: date, as_of: date, opts: Mapping[str, Any]
) -> dict[str, Any]:
    """Weekday residual spend/income over the full calendar-day grid (zero days included)."""
    days = [grid_start + timedelta(days=i) for i in range((as_of - grid_start).days + 1)]
    spend = {d: ZERO for d in days}
    income = {d: ZERO for d in days}
    categories: dict[str, Decimal] = defaultdict(lambda: ZERO)
    for tx in residual:
        if tx["_amount"] < 0:
            spend[tx["_date"]] += tx["_amount"]
            categories[str(tx.get("category_slug") or "uncategorized")] += tx["_amount"]
        else:
            income[tx["_date"]] += tx["_amount"]
    model: dict[str, Any] = {
        "history_days": len(days),
        "status": "ok",
        "spend_by_weekday": {},
        "income_by_weekday": {},
        "category_totals": {k: float(categories[k]) for k in sorted(categories)},
    }
    if len(days) < int(opts["min_history_days"]):
        model["status"] = "insufficient_history"
        model["spend_by_weekday"] = {i: ZERO for i in range(7)}
        model["income_by_weekday"] = {i: ZERO for i in range(7)}
        return model
    q = float(opts["winsor_percentile"])
    pooled_spend = _winsorized_mean([spend[d] for d in days], q)
    pooled_income = _winsorized_mean([income[d] for d in days], q)
    sparse = []
    for weekday in range(7):
        same = [d for d in days if d.weekday() == weekday]
        if len(same) >= int(opts["min_weekday_samples"]):
            model["spend_by_weekday"][weekday] = _winsorized_mean([spend[d] for d in same], q)
            model["income_by_weekday"][weekday] = _winsorized_mean([income[d] for d in same], q)
        else:
            model["spend_by_weekday"][weekday] = pooled_spend
            model["income_by_weekday"][weekday] = pooled_income
            sparse.append(weekday)
    model["pooled_weekdays"] = sparse
    return model


# --------------------------------------------------------------------------- public API


def _rule_to_stream(rule: Any, origin: str) -> dict[str, Any]:
    """Normalize a manual/saved rule mapping into the common stream shape."""
    rule_id = str(_read(rule, "rule_id", _read(rule, "id")))
    raw_cadence = str(_read(rule, "cadence", _read(rule, "frequency", ""))).strip().lower()
    cadence = _SUPPORTED_FREQUENCIES.get(raw_cadence)
    amount = _to_decimal(_read(rule, "amount"))
    stream: dict[str, Any] = {
        "stream_id": rule_id,
        "origin": origin,
        "account_id": None if _read(rule, "account_id") is None else str(_read(rule, "account_id")),
        "merchant_key": _read(rule, "merchant_key"),
        "sign": 1 if amount > 0 else -1,
        "amount": amount,
        "transactions": [],
        "cadence": cadence,
        "status": str(_read(rule, "status", "active")).lower(),
        "days": _read(rule, "days"),
        "anchor": _to_date(_read(rule, "anchor_date", _read(rule, "next_due_date"))),
        "end_date": _read(rule, "end_date"),
        "label": _read(rule, "label"),
        "confidence": 1.0 if origin == "manual" else 0.9,
        "reason": f"{origin}_rule",
        "source_transaction_ids": [str(t) for t in (_read(rule, "source_transaction_ids") or [])],
    }
    if cadence is None:
        stream["reason"] = f"unsupported_cadence:{raw_cadence or 'missing'}"
    return stream


def build_v2_inputs(
    *,
    transactions: Iterable[Any],
    recurring_rules: Iterable[Any] = (),
    manual_rules: Iterable[Any] = (),
    accounts: Iterable[Any],
    as_of_date: date | str,
    start_date: date | str,
    horizon_days: int,
    disabled_source_ids: Iterable[str] = (),
    confirmed_source_ids: Iterable[str] = (),
    options: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Build V2 simulator inputs from history.

    Args:
        transactions: History rows (see module docstring for fields and sign convention).
        recurring_rules: Saved rules ``{rule_id, account_id, merchant_key, amount, cadence,
            anchor_date, source_transaction_ids}``. Unsupported cadences are reported, not guessed.
        manual_rules: User rules, same shape plus ``status`` (``active|confirmed|disabled``),
            optional ``days`` and ``end_date``. Include ``merchant_key`` (and ``account_id``) so
            matching history leaves the residual average.
        accounts: The caller-authorized accounts (``account_id``, ``type``, ...). Transactions
            on other accounts are rejected even if supplied.
        as_of_date: Last date of data to use; later transactions are ignored (no look-ahead).
        start_date: First projected day (usually ``as_of_date + 1``).
        horizon_days: Projection length.
        disabled_source_ids: Rule ids / stream ids that must not be projected.
        confirmed_source_ids: Inferred stream ids promoted regardless of confidence.
        options: Overrides for ``DEFAULT_OPTIONS``.

    Returns:
        ``{"scheduled_events", "residual_events", "proposed_rules", "streams",
        "allocation_audit", "reconciliation", "coverage", "residual_model"}``. Events are
        ``ForecastV2Event`` objects ready for ``simulate_cash_ledger(events=...)``.
    """
    opts = {**DEFAULT_OPTIONS, **(options or {})}
    as_of = _to_date(as_of_date, field_name="as_of_date")
    start = _to_date(start_date, field_name="start_date")
    if not isinstance(horizon_days, int) or horizon_days < 1:
        raise ForecastV2InputError("invalid_horizon", "horizon_days must be a positive integer")
    if start <= as_of:
        raise ForecastV2InputError("invalid_range", "start_date must be after as_of_date")
    end = start + timedelta(days=horizon_days - 1)
    disabled, confirmed = set(map(str, disabled_source_ids)), set(map(str, confirmed_source_ids))
    window_start = as_of - timedelta(days=int(opts["lookback_days"]) - 1)

    account_bucket = {str(_read(a, "account_id")): classify_forecast_account(a) for a in accounts}
    usable, rejected = _prepare(transactions, account_bucket, as_of, window_start)
    audit_by_key, candidates = _classify_basic(usable, account_bucket, opts)

    # Streams: manual > saved rules > inferred. Earlier origins claim their transactions first.
    rule_streams = [_rule_to_stream(r, "manual") for r in manual_rules] + [
        _rule_to_stream(r, "recurring_rule") for r in recurring_rules
    ]
    claimed: dict[str, str] = {}
    streams: list[dict[str, Any]] = []
    for stream in rule_streams:
        members = []
        for tx in candidates:
            if tx["transaction_id"] in claimed:
                continue
            by_id = tx["transaction_id"] in stream["source_transaction_ids"]
            by_merchant = (
                stream["merchant_key"] is not None
                and tx["_merchant"] == str(stream["merchant_key"]).strip().lower()
                and (stream["account_id"] is None or tx["account_id"] == stream["account_id"])
                and (1 if tx["_amount"] > 0 else -1) == stream["sign"]
            )
            if by_id or by_merchant:
                members.append(tx)
        stream["transactions"] = members
        stream["dates"] = sorted({t["_date"] for t in members})
        stream["last_seen"] = stream["dates"][-1] if stream["dates"] else None
        if stream["status"] == "disabled" or stream["stream_id"] in disabled:
            stream["state"] = "disabled"
        elif stream["cadence"] is None:
            stream["state"] = "unsupported"
        else:
            stream["state"] = "promoted"
            for tx in members:
                claimed[tx["transaction_id"]] = stream["stream_id"]
        streams.append(stream)
    suppressed = {(s["account_id"], s["merchant_key"], s["sign"]) for s in streams if s["merchant_key"]}

    unclaimed = [t for t in candidates if t["transaction_id"] not in claimed]
    for stream in _infer_streams(unclaimed, as_of, opts):
        key = (stream["account_id"], stream["merchant_key"], stream["sign"])
        if key in suppressed or (None, key[1], key[2]) in suppressed:
            stream["state"], stream["reason"] = "suppressed", "explicit_rule_for_same_stream"
        elif stream["stream_id"] in disabled:
            stream["state"], stream["reason"] = "disabled", "user_disabled"
        elif stream["cadence"] is None:
            stream["state"] = "ignored"
        elif _lapsed(stream, as_of):
            stream["state"], stream["reason"] = "lapsed", "no_recent_occurrence"
        else:
            enough = len(stream["dates"]) >= int(opts["min_occurrences"])
            is_confirmed = stream["stream_id"] in confirmed
            if is_confirmed or (enough and stream["confidence"] >= float(opts["promote_threshold"])):
                stream["state"] = "promoted"
                if is_confirmed:
                    stream["origin"] = "inferred_confirmed"
                    stream["reason"] = "user_confirmed"
                for tx in stream["transactions"]:
                    claimed[tx["transaction_id"]] = stream["stream_id"]
            else:
                stream["state"] = "proposed"
                stream["reason"] = stream["reason"] or "insufficient_evidence"
        streams.append(stream)

    # Allocate the buckets, one audit entry per transaction.
    audit = [e for e in audit_by_key.values()]
    residual_rows: list[dict[str, Any]] = []
    reason_by_tx: dict[str, str] = {}
    for s in streams:
        if s["state"] in {"proposed", "disabled", "lapsed"}:
            for member in s["transactions"]:
                reason_by_tx.setdefault(member["transaction_id"], f"stream_{s['state']}")
    for tx in candidates:
        owner = claimed.get(tx["transaction_id"])
        if owner:
            audit.append(_entry(tx, "scheduled", "promoted_stream", stream_id=owner))
            continue
        reason = reason_by_tx.get(tx["transaction_id"], "variable_spending")
        residual_rows.append(tx)
        audit.append(_entry(tx, "residual", reason))
    audit.sort(key=lambda e: (e["date"], e["transaction_id"], e["bucket"]))

    # Future scheduled events through the V2 core's calendar expansion.
    specs: list[dict[str, Any]] = []
    for stream in streams:
        if stream["state"] != "promoted":
            continue
        kind = "scheduled_income" if stream["sign"] > 0 else "scheduled_bill"
        if stream["origin"] == "inferred" or stream["origin"] == "inferred_confirmed":
            anchor, days = _next_anchor(stream), stream.get("days")
            end_date = None
        else:
            anchor, days, end_date = stream["anchor"], stream.get("days"), stream.get("end_date")
        specs.append(
            {
                "source": {"manual": "manual", "recurring_rule": "recurring"}.get(stream["origin"], "inferred"),
                "source_id": stream["stream_id"],
                "kind": kind,
                "amount": stream["amount"],
                # Charges on a card are cash-spend proxies with no known funding account.
                "account_id": (
                    None if account_bucket.get(stream["account_id"]) == BUCKET_LIABILITY else stream["account_id"]
                ),
                "cadence": stream["cadence"],
                "anchor_date": anchor,
                "days": days,
                "end_date": end_date,
                "confidence": stream["confidence"],
                "metadata": {
                    "stream_id": stream["stream_id"],
                    "origin": stream["origin"],
                    "label": stream.get("label") or stream.get("merchant_key"),
                    "source_transaction_ids": [t["transaction_id"] for t in stream["transactions"]][-12:],
                },
            }
        )
    scheduled = expand_scheduled_events(specs, start, end)
    next_dates: dict[str, list[str]] = defaultdict(list)
    for event in scheduled:
        next_dates[event.source_id].append(event.date.isoformat())

    # Residual model on the de-recurred, transfer-cleaned posted set, over complete days.
    all_dates = [t["_date"] for t in usable if not t.get("pending")]
    grid_start = max(window_start, min(all_dates)) if all_dates else as_of
    model = _residual_model(residual_rows, grid_start, as_of, opts)
    residual_events: list[ForecastV2Event] = []
    for offset in range(horizon_days):
        day = start + timedelta(days=offset)
        for component, table in (("spend", model["spend_by_weekday"]), ("income", model["income_by_weekday"])):
            amount = table.get(day.weekday(), ZERO)
            if amount == 0:
                continue
            residual_events.append(
                ForecastV2Event(
                    event_id=f"residual:{component}:{day.isoformat()}",
                    date=day,
                    amount=amount,
                    account_id=None,
                    kind="residual",
                    source_id=component,
                    source="residual",
                    confidence=None,
                    metadata={"component": component, "history_days": model["history_days"], "model": model["status"]},
                )
            )

    counts = Counter(e["bucket"] for e in audit)
    totals: dict[str, Decimal] = defaultdict(lambda: ZERO)
    for entry in audit:
        totals[entry["bucket"]] += Decimal(entry["amount"])
    reconciliation = {
        "in_scope_transactions": len(usable),
        "audited_transactions": len(audit),
        "by_bucket_count": {k: counts[k] for k in sorted(counts)},
        "by_bucket_amount": {k: float(totals[k]) for k in sorted(totals)},
        "rejected": rejected,
    }
    history_days = model["history_days"]
    confidence = (
        "insufficient"
        if model["status"] != "ok"
        else "high" if history_days >= 90 else "medium" if history_days >= 45 else "low"
    )

    stream_audit = []
    for stream in sorted(streams, key=lambda s: s["stream_id"]):
        stream_audit.append(
            {
                "stream_id": stream["stream_id"],
                "status": stream["state"],
                "origin": stream["origin"],
                "kind": "income" if stream["sign"] > 0 else "bill",
                "account_id": stream["account_id"],
                "merchant_key": stream.get("merchant_key"),
                "cadence": stream["cadence"],
                "amount": f"{stream['amount']:.2f}",
                "confidence": stream["confidence"],
                "confidence_level": _level(stream["confidence"]),
                "confidence_note": "heuristic score, not a calibrated probability",
                "reason": stream["reason"],
                "source_transaction_ids": [t["transaction_id"] for t in stream["transactions"]],
                "next_dates": next_dates.get(stream["stream_id"], []),
            }
        )
    return {
        "scheduled_events": scheduled,
        "residual_events": residual_events,
        "proposed_rules": [s for s in stream_audit if s["status"] in {"proposed", "lapsed"}],
        "streams": stream_audit,
        "allocation_audit": audit,
        "reconciliation": reconciliation,
        "coverage": {
            "history_days": history_days,
            "confidence": confidence,
            "residual_model": model["status"],
            "pooled_weekdays": model.get("pooled_weekdays", []),
            "as_of_date": as_of.isoformat(),
            "window_start": grid_start.isoformat(),
        },
        "residual_model": {
            "status": model["status"],
            "spend_by_weekday": {str(k): float(v) for k, v in sorted(model["spend_by_weekday"].items())},
            "income_by_weekday": {str(k): float(v) for k, v in sorted(model["income_by_weekday"].items())},
            "category_totals": model["category_totals"],
        },
    }

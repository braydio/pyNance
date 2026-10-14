"""Forecast V2 core: a pure, deterministic, event-driven liquid-cash ledger.

Nothing here touches the database, the clock or the network. Callers (the V2 API adapter
in a later packet) must hand in only the authenticated user's accounts and events.

Public API:
    classify_forecast_account  - bucket an account as cash/liability/investment/...
    expand_scheduled_events    - turn recurrence rules into dated events
    simulate_cash_ledger       - build the per-day ledger and summary

Conventions (see ``ForecastV2Event`` for the full sign table):
    * Every amount is a ``Decimal`` quantized to cents at ingestion, so all ledger
      invariants hold exactly, not merely within tolerance.
    * ``starting_cash`` of the first day is the end-of-day balance of the day *before*
      ``start_date``; events dated ``start_date`` apply exactly once.
    * Cash, debt, investments and net worth are separate fields.
"""

from __future__ import annotations

import calendar
import re
from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from typing import Any, Optional

from .models import ForecastV2DailyPoint, ForecastV2Event, ForecastV2Result

CENT = Decimal("0.01")
MAX_HORIZON_DAYS = 3660

BUCKET_CASH = "cash"
BUCKET_LIABILITY = "liability"
BUCKET_INVESTMENT = "investment"
BUCKET_OTHER_ASSET = "other_asset"
BUCKET_UNKNOWN = "unknown"

EVENT_KINDS = frozenset(
    {
        "scheduled_income",
        "scheduled_bill",
        "adjustment",
        "residual",
        "transfer",
        "liability_payment",
        "liability_charge",
    }
)
_CASH_EFFECT_KINDS = frozenset({"scheduled_income", "scheduled_bill", "adjustment", "residual"})
_MOVEMENT_KINDS = frozenset({"transfer", "liability_payment"})
CADENCES = frozenset({"once", "daily", "weekly", "biweekly", "semimonthly", "monthly"})

DEFAULT_ASSUMPTIONS: dict[str, Any] = {"stale_snapshot_days": 3}
_SECRET_KEYS = frozenset({"access_token", "public_token", "item_id", "password", "secret", "token"})

_CASH_TYPES = {"checking", "savings", "cash", "cash management", "money market"}
_LIABILITY_TOKENS = ("credit", "loan", "mortgage", "debt", "line of credit", "liability")
_INVESTMENT_TOKENS = (
    "investment",
    "brokerage",
    "401k",
    "403b",
    "ira",
    "roth",
    "retirement",
    "pension",
    "crypto",
)
_OTHER_ASSET_TOKENS = ("property", "real estate", "vehicle", "other asset")


class ForecastV2InputError(ValueError):
    """Invalid V2 input. ``code`` is a stable machine-readable reason."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


# --------------------------------------------------------------------------- parsing


def _to_decimal(value: Any, *, field_name: str = "amount") -> Decimal:
    """Parse a number into a cent-quantized Decimal (floats go through ``str``)."""
    if isinstance(value, bool) or value is None:
        raise ForecastV2InputError("invalid_amount", f"{field_name} must be a number, got {value!r}")
    try:
        parsed = value if isinstance(value, Decimal) else Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise ForecastV2InputError("invalid_amount", f"{field_name} is not numeric: {value!r}") from exc
    if not parsed.is_finite():
        raise ForecastV2InputError("invalid_amount", f"{field_name} must be finite")
    return parsed.quantize(CENT, rounding=ROUND_HALF_EVEN)


def _to_date(value: Any, *, field_name: str = "date") -> date:
    """Parse ``YYYY-MM-DD`` strings, dates and datetimes into a date."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value.strip()[:10])
        except ValueError:
            pass
    raise ForecastV2InputError("invalid_date", f"{field_name} is not a valid date: {value!r}")


def _norm_text(value: Any) -> str:
    return re.sub(r"[\s_/\-]+", " ", str(value or "").strip().lower())


def _json_safe(value: Any) -> Any:
    """Return JSON-safe provenance with secret-looking keys dropped."""
    if isinstance(value, Mapping):
        return {
            str(key): _json_safe(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
            if _norm_text(key) not in {_norm_text(secret) for secret in _SECRET_KEYS}
        }
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _read(entry: Any, key: str, default: Any = None) -> Any:
    if isinstance(entry, Mapping):
        return entry.get(key, default)
    return getattr(entry, key, default)


# --------------------------------------------------------------------------- accounts


def classify_forecast_account(account: Any) -> str:
    """Bucket an account for the V2 ledger.

    Returns ``cash``, ``liability``, ``investment``, ``other_asset`` or ``unknown``.
    Only explicit depository checking/savings/cash types are ``cash``; anything that
    cannot be classified is ``unknown`` and never silently treated as spendable cash.

    Args:
        account: Mapping/object with ``type``, optional ``subtype`` and ``is_investment``.
    """
    acct_type = _norm_text(_read(account, "type"))
    subtype = _norm_text(_read(account, "subtype"))
    combined = f"{acct_type} {subtype}".strip()

    if any(token in combined for token in _LIABILITY_TOKENS):
        return BUCKET_LIABILITY
    if _read(account, "is_investment") or any(token in combined for token in _INVESTMENT_TOKENS):
        return BUCKET_INVESTMENT
    if acct_type in _CASH_TYPES:
        return BUCKET_CASH
    if acct_type == "depository":
        return BUCKET_CASH if subtype in _CASH_TYPES else BUCKET_UNKNOWN
    if any(token in combined for token in _OTHER_ASSET_TOKENS):
        return BUCKET_OTHER_ASSET
    return BUCKET_UNKNOWN


# --------------------------------------------------------------------------- recurrence


def _clamp_day(year: int, month: int, day: int) -> date:
    return date(year, month, min(day, calendar.monthrange(year, month)[1]))


def _month_iter(first: date, last: date):
    year, month = first.year, first.month
    while (year, month) <= (last.year, last.month):
        yield year, month
        month += 1
        if month > 12:
            year, month = year + 1, 1


def _occurrence_dates(
    cadence: str, anchor: date, window_start: date, window_end: date, semimonthly_days: Sequence[int]
) -> list[date]:
    """Dates in ``[window_start, window_end]`` that a rule anchored at ``anchor`` fires on.

    Monthly rules keep the *original* anchor day (31 -> Feb 28/29 -> Mar 31); nothing
    drifts after a short month. No occurrence is generated before ``anchor``.
    """
    first = max(anchor, window_start)
    if first > window_end:
        return []
    if cadence == "once":
        return [anchor] if window_start <= anchor <= window_end else []
    if cadence in {"daily", "weekly", "biweekly"}:
        step = {"daily": 1, "weekly": 7, "biweekly": 14}[cadence]
        offset = (first - anchor).days
        start = anchor + timedelta(days=-(-offset // step) * step)
        out, current = [], start
        while current <= window_end:
            out.append(current)
            current += timedelta(days=step)
        return out
    if cadence == "monthly":
        return [
            d
            for year, month in _month_iter(first, window_end)
            if first <= (d := _clamp_day(year, month, anchor.day)) <= window_end
        ]
    if cadence == "semimonthly":
        out = []
        for year, month in _month_iter(first, window_end):
            for day in sorted(semimonthly_days):
                d = _clamp_day(year, month, day)
                if anchor <= d and first <= d <= window_end:
                    out.append(d)
        return out
    raise ForecastV2InputError("invalid_cadence", f"Unsupported cadence {cadence!r}")


def _event_id(source: str, source_id: Any, day: date, suffix: str = "") -> str:
    return f"{source}:{source_id}:{day.isoformat()}{suffix}"


def _build_event(spec: Any, day: date, event_id: str, amount: Decimal) -> ForecastV2Event:
    kind = str(_read(spec, "kind", "")).strip()
    confidence = _read(spec, "confidence")
    return ForecastV2Event(
        event_id=event_id,
        date=day,
        amount=amount,
        account_id=None if _read(spec, "account_id") is None else str(_read(spec, "account_id")),
        kind=kind,
        source_id=None if _read(spec, "source_id") is None else str(_read(spec, "source_id")),
        source=str(_read(spec, "source", "manual")),
        confidence=None if confidence is None else float(confidence),
        counterparty_account_id=(
            None if _read(spec, "counterparty_account_id") is None else str(_read(spec, "counterparty_account_id"))
        ),
        override=bool(_read(spec, "override", False)),
        metadata=_json_safe(_read(spec, "metadata", {}) or {}),
    )


def _validate_event(event: ForecastV2Event) -> None:
    if event.kind not in EVENT_KINDS:
        raise ForecastV2InputError("invalid_kind", f"Unknown event kind {event.kind!r} ({event.event_id})")
    if event.kind == "scheduled_income" and event.amount <= 0:
        raise ForecastV2InputError("invalid_amount", f"scheduled_income must be positive ({event.event_id})")
    if event.kind == "scheduled_bill" and event.amount >= 0:
        raise ForecastV2InputError("invalid_amount", f"scheduled_bill must be negative ({event.event_id})")
    if event.kind not in _CASH_EFFECT_KINDS and event.amount <= 0:
        raise ForecastV2InputError(
            "invalid_amount", f"{event.kind} amount must be a positive magnitude ({event.event_id})"
        )


def expand_scheduled_events(
    specs: Iterable[Any], window_start: date | str, window_end: date | str
) -> list[ForecastV2Event]:
    """Expand recurrence rules into concrete events inside ``[window_start, window_end]``.

    A spec is a mapping with ``source_id``, ``kind``, ``amount``, ``account_id``,
    ``cadence`` (``once|daily|weekly|biweekly|semimonthly|monthly``) and ``anchor_date``.
    Optional: ``end_date`` (last effective day), ``days`` (exactly two month days, required
    for ``semimonthly``), ``counterparty_account_id``, ``source``, ``confidence``,
    ``override`` and ``metadata``. Events never fall outside the window or before the anchor.

    Raises:
        ForecastV2InputError: bad cadence, date, range or semimonthly days.
    """
    start = _to_date(window_start, field_name="window_start")
    end = _to_date(window_end, field_name="window_end")
    events: list[ForecastV2Event] = []
    for spec in specs:
        cadence = str(_read(spec, "cadence", "once")).strip().lower()
        if cadence not in CADENCES:
            raise ForecastV2InputError("invalid_cadence", f"Unsupported cadence {cadence!r}")
        anchor = _to_date(_read(spec, "anchor_date", _read(spec, "date")), field_name="anchor_date")
        last_effective = _read(spec, "end_date")
        effective_end = end
        if last_effective is not None:
            last = _to_date(last_effective, field_name="end_date")
            if last < anchor:
                raise ForecastV2InputError("invalid_range", "end_date precedes anchor_date")
            effective_end = min(end, last)
        days: Sequence[int] = ()
        if cadence == "semimonthly":
            raw_days = _read(spec, "days")
            try:
                days = tuple(int(d) for d in raw_days)
            except (TypeError, ValueError):
                days = ()
            if len(days) != 2 or len(set(days)) != 2 or any(not 1 <= d <= 31 for d in days):
                raise ForecastV2InputError(
                    "invalid_semimonthly_days", "semimonthly requires two distinct days of month (1-31)"
                )
        amount = _to_decimal(_read(spec, "amount"))
        source = str(_read(spec, "source", "manual"))
        source_id = _read(spec, "source_id")
        seen: dict[str, int] = {}
        for day in _occurrence_dates(cadence, anchor, start, effective_end, days):
            base = _event_id(source, source_id, day)
            seen[base] = seen.get(base, 0) + 1
            # Two semimonthly days can clamp onto one date; keep both as distinct events.
            suffix = "" if seen[base] == 1 else f"#{seen[base]}"
            event = _build_event(spec, day, base + suffix, amount)
            _validate_event(event)
            events.append(event)
    return sorted(events, key=lambda e: (e.date, e.event_id))


def _expand_adjustments(adjustments: Iterable[Any], start: date, end: date) -> list[ForecastV2Event]:
    """Convert V1-style manual adjustments to ``adjustment`` events inside the horizon.

    ``distribution: spread`` splits the amount across the in-horizon days of
    ``range_start..range_end`` to the cent, giving any remainder to the last day so the
    total is preserved exactly. ``frequency`` supports once/daily/weekly/biweekly/monthly.
    """
    events: list[ForecastV2Event] = []
    for index, adjustment in enumerate(adjustments):
        amount = _to_decimal(_read(adjustment, "amount", 0))
        if amount == 0:
            continue
        source_id = _read(adjustment, "adjustment_id", _read(adjustment, "id", f"adj{index + 1}"))
        base = {
            "kind": "adjustment",
            "source": "manual",
            "source_id": source_id,
            "account_id": _read(adjustment, "account_id"),
            "metadata": {"label": _read(adjustment, "label"), "reason": _read(adjustment, "reason")},
        }
        distribution = str(_read(adjustment, "distribution", "single")).strip().lower()
        if distribution in {"spread", "distributed"}:
            first = _to_date(_read(adjustment, "range_start") or _read(adjustment, "date"), field_name="range_start")
            last = _to_date(_read(adjustment, "range_end") or _read(adjustment, "date"), field_name="range_end")
            if last < first:
                first, last = last, first
            span = [first + timedelta(days=i) for i in range((last - first).days + 1)]
            days = [d for d in span if start <= d <= end]
            if not days:
                continue
            share = (amount / len(days)).quantize(CENT, rounding=ROUND_HALF_EVEN)
            amounts = [share] * (len(days) - 1) + [amount - share * (len(days) - 1)]
            for day, part in zip(days, amounts):
                events.append(_build_event(base, day, _event_id("manual", source_id, day), part))
            continue
        frequency = _read(adjustment, "frequency")
        cadence = "once" if not frequency else str(frequency).strip().lower()
        spec = {
            **base,
            "amount": amount,
            "cadence": cadence,
            "anchor_date": _read(adjustment, "date") or _read(adjustment, "start_date") or start,
        }
        events.extend(expand_scheduled_events([spec], start, end))
    return events


# --------------------------------------------------------------------------- simulation


class _Warnings:
    def __init__(self) -> None:
        self._items: list[dict[str, Any]] = []

    def add(self, code: str, message: str, **context: Any) -> None:
        self._items.append({"code": code, "message": message, **context})

    def sorted(self) -> list[dict[str, Any]]:
        return sorted(
            self._items,
            key=lambda w: (w["code"], str(w.get("account_id", "")), str(w.get("event_id", "")), w["message"]),
        )


def _dedupe(events: list[ForecastV2Event], warnings: _Warnings) -> list[ForecastV2Event]:
    """Collapse events sharing an ``event_id``; an ``override`` wins, else the first seen."""
    chosen: dict[str, ForecastV2Event] = {}
    for event in events:
        current = chosen.get(event.event_id)
        if current is None:
            chosen[event.event_id] = event
        elif event.override and not current.override:
            chosen[event.event_id] = event
            warnings.add("duplicate_event_replaced", "Override replaced a scheduled instance", event_id=event.event_id)
        else:
            warnings.add("duplicate_event_dropped", "Duplicate event instance ignored", event_id=event.event_id)
    return sorted(chosen.values(), key=lambda e: (e.date, e.event_id))


def _eligible_accounts(
    snapshots: Iterable[Any], owner_id: Any, start: date, stale_days: int, warnings: _Warnings
) -> tuple[dict[str, str], dict[str, Decimal], list[str]]:
    """Return ``(bucket_by_id, opening_balance_by_id, excluded_ids)`` for the user."""
    bucket_by_id: dict[str, str] = {}
    balance_by_id: dict[str, Decimal] = {}
    excluded: list[str] = []
    for snapshot in snapshots:
        raw_id = _read(snapshot, "account_id")
        if raw_id is None:
            warnings.add("account_missing_id", "Account without an id was skipped")
            continue
        account_id = str(raw_id)
        if owner_id is not None and _read(snapshot, "user_id") not in (None, owner_id):
            warnings.add("account_not_authorized", "Account belongs to another user", account_id=account_id)
            excluded.append(account_id)
            continue
        if _read(snapshot, "is_hidden") or _read(snapshot, "excluded"):
            warnings.add("account_hidden", "Hidden or excluded account left out", account_id=account_id)
            excluded.append(account_id)
            continue
        bucket = classify_forecast_account(snapshot)
        if bucket == BUCKET_UNKNOWN:
            warnings.add(
                "unknown_account_type",
                f"Account type {_read(snapshot, 'type')!r}/{_read(snapshot, 'subtype')!r} is not classified; excluded",
                account_id=account_id,
            )
            excluded.append(account_id)
            continue
        if _read(snapshot, "balance") is None:
            warnings.add("missing_balance", "Account has no balance and was left out", account_id=account_id)
            excluded.append(account_id)
            continue
        balance = _to_decimal(_read(snapshot, "balance"), field_name="balance")
        if bucket == BUCKET_LIABILITY:
            balance = abs(balance)  # amount owed; liability sign conventions vary by provider
        as_of = _read(snapshot, "as_of")
        if as_of is not None:
            age = (start - timedelta(days=1) - _to_date(as_of, field_name="as_of")).days
            if age > stale_days:
                warnings.add("stale_snapshot", f"Balance is {age} days old", account_id=account_id, age_days=age)
        if account_id in bucket_by_id:
            warnings.add("duplicate_account", "Duplicate account snapshot ignored", account_id=account_id)
            continue
        bucket_by_id[account_id] = bucket
        balance_by_id[account_id] = balance
    return bucket_by_id, balance_by_id, sorted(set(excluded))


def simulate_cash_ledger(
    *,
    start_date: date | str,
    horizon_days: int,
    account_snapshots: Iterable[Any],
    events: Iterable[Any] = (),
    cash_adjustments: Iterable[Any] = (),
    assumptions: Optional[Mapping[str, Any]] = None,
    owner_id: Any = None,
) -> ForecastV2Result:
    """Project liquid cash day by day from dated events.

    Args:
        start_date: First projected day. The opening balance is the end of the previous day.
        horizon_days: Number of calendar days to project (1..3660).
        account_snapshots: Accounts with ``account_id``, ``type``, ``subtype``, ``balance`` and
            optional ``is_investment``, ``is_hidden``, ``user_id``, ``as_of``. Liability
            ``balance`` is the amount owed.
        events: Concrete events (``ForecastV2Event`` or mappings with ``date``) and/or
            recurrence specs (mappings with ``cadence``), expanded over the horizon.
        cash_adjustments: V1-style manual adjustments, applied once each (see
            ``_expand_adjustments``).
        assumptions: Optional overrides of ``DEFAULT_ASSUMPTIONS``.
        owner_id: When given, accounts whose ``user_id`` differs are excluded. Defence in
            depth only: the adapter must already pass just the owner's data.

    Returns:
        ``ForecastV2Result``. ``status`` is ``insufficient_data`` (no daily points) when
        no eligible liquid-cash account exists.

    Raises:
        ForecastV2InputError: non-positive/oversized horizon, invalid date/cadence/amount/kind.
    """
    start = _to_date(start_date, field_name="start_date")
    if not isinstance(horizon_days, int) or isinstance(horizon_days, bool) or not 1 <= horizon_days <= MAX_HORIZON_DAYS:
        raise ForecastV2InputError("invalid_horizon", f"horizon_days must be 1..{MAX_HORIZON_DAYS}")
    end = start + timedelta(days=horizon_days - 1)
    settings = {**DEFAULT_ASSUMPTIONS, **(assumptions or {})}
    warnings = _Warnings()

    bucket_by_id, opening, excluded = _eligible_accounts(
        account_snapshots, owner_id, start, int(settings["stale_snapshot_days"]), warnings
    )
    accounts_meta = {
        "included": {
            bucket: sorted(a for a, b in bucket_by_id.items() if b == bucket)
            for bucket in (BUCKET_CASH, BUCKET_LIABILITY, BUCKET_INVESTMENT, BUCKET_OTHER_ASSET)
        },
        "excluded": excluded,
    }
    if not accounts_meta["included"][BUCKET_CASH]:
        warnings.add("no_liquid_cash_accounts", "No eligible checking/savings/cash account to project")
        return ForecastV2Result(
            status="insufficient_data",
            start_date=start,
            end_date=end,
            horizon_days=horizon_days,
            accounts=accounts_meta,
            warnings=warnings.sorted(),
        )

    # ---- gather events ------------------------------------------------------------
    gathered: list[ForecastV2Event] = []
    specs: list[Any] = []
    for position, item in enumerate(events):
        if isinstance(item, ForecastV2Event):
            _validate_event(item)
            gathered.append(item)
        elif _read(item, "cadence") is not None:
            specs.append(item)
        else:
            day = _to_date(_read(item, "date"), field_name="event date")
            source = str(_read(item, "source", "manual"))
            # Without an explicit id, position keeps distinct same-day events distinct.
            event_id = _read(item, "event_id") or _event_id(
                source, _read(item, "source_id", f"event{position + 1}"), day
            )
            event = _build_event(item, day, str(event_id), _to_decimal(_read(item, "amount")))
            _validate_event(event)
            gathered.append(event)
    gathered.extend(expand_scheduled_events(specs, start, end))
    gathered.extend(_expand_adjustments(cash_adjustments, start, end))

    in_horizon = [e for e in gathered if start <= e.date <= end]
    outside = len(gathered) - len(in_horizon)
    ordered = _dedupe(sorted(in_horizon, key=lambda e: (e.date, e.event_id, not e.override)), warnings)

    # ---- ledger -------------------------------------------------------------------
    cash = {a: opening[a] for a in accounts_meta["included"][BUCKET_CASH]}
    liability = {a: opening[a] for a in accounts_meta["included"][BUCKET_LIABILITY]}
    investment = {a: opening[a] for a in accounts_meta["included"][BUCKET_INVESTMENT]}
    other = {a: opening[a] for a in accounts_meta["included"][BUCKET_OTHER_ASSET]}
    zero = Decimal("0.00")

    def is_cash(acct: Optional[str]) -> bool:
        return acct is not None and acct in cash

    applied: list[ForecastV2Event] = []
    by_day: dict[date, list[ForecastV2Event]] = {}
    for event in ordered:
        by_day.setdefault(event.date, []).append(event)

    def apply(event: ForecastV2Event) -> Optional[tuple[Decimal, bool]]:
        """Apply an event; return ``(cash_delta, internal)`` or ``None`` when dropped."""
        kind, amount, src, dst = event.kind, event.amount, event.account_id, event.counterparty_account_id
        if kind in _CASH_EFFECT_KINDS:
            if src is None:  # no known funding account: consolidated cash only
                cash["unassigned"] = cash.get("unassigned", zero) + amount
                return amount, False
            if not is_cash(src):
                warnings.add(
                    "event_account_not_cash",
                    "Event targets an account that is not an included liquid-cash account",
                    event_id=event.event_id,
                    account_id=src,
                )
                return None
            cash[src] += amount
            return amount, False
        if kind == "liability_charge":
            if src not in liability:
                warnings.add(
                    "event_account_not_liability",
                    "Charge targets an account that is not an included liability",
                    event_id=event.event_id,
                    account_id=src,
                )
                return None
            liability[src] += amount
            return zero, False
        # transfer / liability_payment: ``src`` gives up value, ``dst`` receives it.
        src_in = src in cash or src in investment or src in other
        if src in liability:
            warnings.add(
                "unsupported_transfer_source", "Transfers out of a liability are unsupported", event_id=event.event_id
            )
            return None
        dst_in = dst in cash or dst in investment or dst in other or dst in liability
        if not src_in and not dst_in:
            warnings.add("event_unscoped", "Transfer touches no included account", event_id=event.event_id)
            return None
        delta = zero
        if src in cash:
            cash[src] -= amount
            delta -= amount
        elif src in investment:
            investment[src] -= amount
        elif src in other:
            other[src] -= amount
        if dst in cash:
            cash[dst] += amount
            delta += amount
        elif dst in investment:
            investment[dst] += amount
        elif dst in other:
            other[dst] += amount
        elif dst in liability:
            if amount > liability[dst]:
                warnings.add(
                    "liability_overpaid",
                    "Payment exceeds the modeled balance owed; balance floored at zero",
                    event_id=event.event_id,
                    account_id=dst,
                )
            liability[dst] = max(zero, liability[dst] - amount)
        internal = src in cash and dst in cash
        return delta, internal

    daily: list[ForecastV2DailyPoint] = []
    by_kind: dict[str, Decimal] = {}
    total_in = total_out = total_adj = zero
    for offset in range(horizon_days):
        day = start + timedelta(days=offset)
        starting = sum(cash.values(), zero)
        inflows = outflows = adjustments = zero
        ids: list[str] = []
        for event in by_day.get(day, ()):
            outcome = apply(event)
            if outcome is None:
                continue
            delta, internal = outcome
            applied.append(event)
            ids.append(event.event_id)
            by_kind[event.kind] = by_kind.get(event.kind, zero) + delta
            if event.kind == "adjustment":
                adjustments += delta
            elif internal or delta == 0:
                continue
            elif delta > 0:
                inflows += delta
            else:
                outflows += -delta
        ending = sum(cash.values(), zero)
        owed, invested, others = (
            sum(liability.values(), zero),
            sum(investment.values(), zero),
            sum(other.values(), zero),
        )
        daily.append(
            ForecastV2DailyPoint(
                date=day,
                starting_cash=starting,
                inflows=inflows,
                outflows=outflows,
                adjustments=adjustments,
                ending_cash=ending,
                event_ids=ids,
                cash_by_account=dict(cash),
                liability_balance=owed,
                investment_value=invested,
                other_assets=others,
                net_worth=ending + others + invested - owed,
            )
        )
        total_in, total_out, total_adj = total_in + inflows, total_out + outflows, total_adj + adjustments

    low = min(daily, key=lambda p: (p.ending_cash, p.date))
    high = max(daily, key=lambda p: (p.ending_cash, -p.date.toordinal()))
    first_negative = next((p.date for p in daily if p.ending_cash < 0), None)
    starting_cash = daily[0].starting_cash
    opening_other = sum((opening[a] for a in accounts_meta["included"][BUCKET_OTHER_ASSET]), zero)
    opening_inv = sum((opening[a] for a in accounts_meta["included"][BUCKET_INVESTMENT]), zero)
    opening_debt = sum((opening[a] for a in accounts_meta["included"][BUCKET_LIABILITY]), zero)
    starting_net = starting_cash + opening_other + opening_inv - opening_debt

    summary = {
        "starting_cash": float(starting_cash),
        "ending_cash": float(daily[-1].ending_cash),
        "net_change": float(daily[-1].ending_cash - starting_cash),
        "total_inflows": float(total_in),
        "total_outflows": float(total_out),
        "total_adjustments": float(total_adj),
        "min_cash": float(low.ending_cash),
        "min_cash_date": low.date.isoformat(),
        "max_cash": float(high.ending_cash),
        "first_negative_date": first_negative.isoformat() if first_negative else None,
        "starting_net_worth": float(starting_net),
        "ending_net_worth": float(daily[-1].net_worth),
        "by_kind": {kind: float(by_kind[kind]) for kind in sorted(by_kind)},
        "event_count": len(applied),
        "events_outside_horizon": outside,
        "currency": settings.get("currency", "USD"),
    }
    return ForecastV2Result(
        status="ok",
        start_date=start,
        end_date=end,
        horizon_days=horizon_days,
        daily=daily,
        events=applied,
        summary=summary,
        accounts=accounts_meta,
        warnings=warnings.sorted(),
    )

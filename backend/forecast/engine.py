"""Forecast projection helpers for balance timelines."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from .models import DateLike, ForecastCashflowItem, ForecastTimelinePoint

DEFAULT_CATEGORY_CONFIDENCE = Decimal("0.6")
DEFAULT_RECURRING_CONFIDENCE = Decimal("0.85")
DEFAULT_UNCATEGORIZED_CONFIDENCE = Decimal("0.3")
DEFAULT_ADJUSTMENT_CONFIDENCE = Decimal("0.95")


def _parse_date(value: DateLike | None, fallback: date) -> date:
    """Return a date instance from a date-like value."""
    if value is None:
        return fallback
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.fromisoformat(value).date()


def _to_decimal(value: Any) -> Decimal:
    """Coerce numeric values into a Decimal, defaulting to zero on bad input."""
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0")


def _extract_amount(entry: Mapping[str, Any], keys: Iterable[str]) -> Decimal:
    """Pull the first available numeric amount from a mapping."""
    for key in keys:
        if key in entry and entry[key] is not None:
            return _to_decimal(entry[key])
    return Decimal("0")


def _read_entry_value(entry: Any, key: str, fallback: Any = None) -> Any:
    """Return a value from a mapping or attribute with a fallback."""
    if isinstance(entry, Mapping):
        return entry.get(key, fallback)
    return getattr(entry, key, fallback)


def _normalize_frequency(value: Any) -> str | None:
    """Normalize frequency values to supported cadence tokens."""
    if value is None:
        return None
    normalized = str(value).strip().lower()
    if normalized in {"once", "one-time", "onetime", "single"}:
        return None
    if normalized in {"daily", "weekly", "monthly"}:
        return normalized
    return None


def _matches_frequency(
    current_date: date, start_date: date, frequency: str | None
) -> bool:
    """Return True when a date matches a recurring frequency."""
    if current_date < start_date:
        return False
    if frequency is None:
        return current_date == start_date
    if frequency == "daily":
        return True
    if frequency == "weekly":
        return (current_date - start_date).days % 7 == 0
    if frequency == "monthly":
        return current_date.day == start_date.day
    return False


def _cashflow_direction(amount: Decimal) -> str:
    """Return the cashflow direction for a signed amount."""
    return "inflow" if amount >= 0 else "outflow"


def _cashflow_type(amount: Decimal) -> str:
    """Return the cashflow type for a signed amount."""
    return "income" if amount >= 0 else "expense"


def _daily_deltas(
    timeline: Sequence[ForecastTimelinePoint],
) -> list[tuple[date, Decimal]]:
    """Return daily balance deltas keyed by date in timeline order."""
    deltas: list[tuple[date, Decimal]] = []
    if not timeline:
        return deltas

    first_point = timeline[0]
    first_balance = _to_decimal(first_point.forecast_balance)
    metadata = first_point.metadata or {}
    if "starting_balance" in metadata:
        previous_balance = _to_decimal(metadata.get("starting_balance"))
    elif "average_inflow" in metadata and "average_outflow" in metadata:
        average_inflow = _to_decimal(metadata.get("average_inflow"))
        average_outflow = _to_decimal(metadata.get("average_outflow"))
        previous_balance = first_balance - (average_inflow - average_outflow)
    else:
        previous_balance = first_balance

    for point in timeline:
        current_date = _parse_date(point.date, fallback=date.today())
        current_balance = _to_decimal(point.forecast_balance)
        delta = current_balance - previous_balance
        deltas.append((current_date, delta))
        previous_balance = current_balance

    return deltas


def _category_sources(
    category_averages: Sequence[Mapping[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Normalize category averages into source dictionaries."""
    if not category_averages:
        return []

    sources: list[dict[str, Any]] = []
    inflow_keys = (
        "inflow",
        "inflows",
        "income",
        "credit",
        "average_inflow",
        "avg_inflow",
    )
    outflow_keys = (
        "outflow",
        "outflows",
        "expense",
        "debit",
        "average_outflow",
        "avg_outflow",
    )
    amount_keys = ("amount", "average", "avg", "net", "value")

    for entry in category_averages:
        label = str(
            entry.get("category")
            or entry.get("label")
            or entry.get("name")
            or "Uncategorized"
        )
        confidence = _to_decimal(entry.get("confidence", DEFAULT_CATEGORY_CONFIDENCE))

        inflow = _extract_amount(entry, inflow_keys)
        outflow = _extract_amount(entry, outflow_keys)
        explicit_amount = _extract_amount(entry, amount_keys)

        if inflow:
            sources.append(
                {
                    "label": label,
                    "category": label,
                    "amount": inflow,
                    "confidence": confidence,
                    "source": "category_average",
                }
            )
        if outflow:
            sources.append(
                {
                    "label": label,
                    "category": label,
                    "amount": -outflow,
                    "confidence": confidence,
                    "source": "category_average",
                }
            )
        if not inflow and not outflow and explicit_amount:
            direction = str(entry.get("direction") or entry.get("type") or "").lower()
            amount = explicit_amount
            if direction == "expense" and amount > 0:
                amount = -amount
            sources.append(
                {
                    "label": label,
                    "category": label,
                    "amount": amount,
                    "confidence": confidence,
                    "source": "category_average",
                }
            )

    return sources


def _recurring_sources_by_date(
    recurring_sources: Sequence[Mapping[str, Any]] | None,
    timeline_dates: Sequence[date],
) -> dict[date, list[dict[str, Any]]]:
    """Expand recurring source labels across timeline dates."""
    expanded: dict[date, list[dict[str, Any]]] = {day: [] for day in timeline_dates}
    if not recurring_sources or not timeline_dates:
        return expanded

    for entry in recurring_sources:
        start_date = _parse_date(
            entry.get("date") or entry.get("start_date"),
            fallback=timeline_dates[0],
        )
        frequency = _normalize_frequency(entry.get("frequency"))
        amount = _to_decimal(entry.get("amount"))
        if not amount:
            continue

        label = str(
            entry.get("label")
            or entry.get("merchant")
            or entry.get("description")
            or "Recurring"
        )
        category = str(entry.get("category") or "Recurring")
        confidence = _to_decimal(entry.get("confidence", DEFAULT_RECURRING_CONFIDENCE))
        metadata = {
            "frequency": frequency or "one-time",
            "recurring_id": entry.get("recurring_id"),
        }

        for current_date in timeline_dates:
            if _matches_frequency(current_date, start_date, frequency):
                expanded[current_date].append(
                    {
                        "label": label,
                        "category": category,
                        "amount": amount,
                        "confidence": confidence,
                        "source": "recurring",
                        "metadata": metadata,
                    }
                )
                if frequency is None:
                    break

    return expanded


def _scaled_category_items(
    remaining: Decimal, category_sources: Sequence[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Scale category averages to match the remaining delta."""
    if not category_sources or remaining == 0:
        return []

    category_total = sum(
        (_to_decimal(source.get("amount")) for source in category_sources), Decimal("0")
    )
    if category_total == 0:
        return []

    scale = remaining / category_total
    scaled_items: list[dict[str, Any]] = []
    for source in category_sources:
        amount = _to_decimal(source.get("amount")) * scale
        if amount == 0:
            continue
        scaled_items.append(
            {
                "label": source.get("label"),
                "category": source.get("category"),
                "amount": amount,
                "confidence": source.get("confidence", DEFAULT_CATEGORY_CONFIDENCE),
                "source": source.get("source", "category_average"),
            }
        )
    return scaled_items


def build_cashflow_items(
    timeline: Sequence[ForecastTimelinePoint],
    *,
    category_averages: Sequence[Mapping[str, Any]] | None = None,
    recurring_sources: Sequence[Mapping[str, Any]] | None = None,
    adjustments: Sequence[Mapping[str, Any]] | None = None,
    uncategorized_label: str = "Uncategorized",
) -> list[ForecastCashflowItem]:
    """Build cashflow items for each balance delta and adjustment.

    Args:
        timeline: Baseline forecast timeline points.
        category_averages: Optional category averages used for source labels.
        recurring_sources: Optional recurring merchant labels to attribute cashflows.
        adjustments: Optional adjustments to include in the breakdown.
        uncategorized_label: Label to use when no source attribution exists.

    Returns:
        List of :class:`ForecastCashflowItem` entries.
    """
    cashflows: list[ForecastCashflowItem] = []
    if not timeline:
        return cashflows

    daily_deltas = _daily_deltas(timeline)
    timeline_dates = [day for day, _ in daily_deltas]
    category_sources = _category_sources(category_averages)
    recurring_by_date = _recurring_sources_by_date(recurring_sources, timeline_dates)

    for current_date, delta in daily_deltas:
        day_items: list[tuple[Decimal, ForecastCashflowItem]] = []
        recurring_items = recurring_by_date.get(current_date, [])
        recurring_total = sum(
            (_to_decimal(item.get("amount")) for item in recurring_items), Decimal("0")
        )

        for entry in recurring_items:
            amount = _to_decimal(entry.get("amount"))
            if amount == 0:
                continue
            day_items.append(
                (
                    amount,
                    ForecastCashflowItem(
                        date=current_date,
                        amount=float(amount),
                        label=str(entry.get("label")),
                        category=str(entry.get("category") or "Recurring"),
                        source=str(entry.get("source") or "recurring"),
                        type=_cashflow_type(amount),
                        confidence=float(
                            entry.get("confidence", DEFAULT_RECURRING_CONFIDENCE)
                        ),
                        direction=_cashflow_direction(amount),
                        metadata=entry.get("metadata", {}),
                    ),
                )
            )

        remaining = delta - recurring_total
        for entry in _scaled_category_items(remaining, category_sources):
            amount = _to_decimal(entry.get("amount"))
            if amount == 0:
                continue
            day_items.append(
                (
                    amount,
                    ForecastCashflowItem(
                        date=current_date,
                        amount=float(amount),
                        label=str(entry.get("label")),
                        category=str(entry.get("category") or uncategorized_label),
                        source=str(entry.get("source") or "category_average"),
                        type=_cashflow_type(amount),
                        confidence=float(
                            entry.get("confidence", DEFAULT_CATEGORY_CONFIDENCE)
                        ),
                        direction=_cashflow_direction(amount),
                        metadata={},
                    ),
                )
            )

        daily_total = sum((amount for amount, _ in day_items), Decimal("0"))
        remainder = delta - daily_total
        if remainder != 0:
            day_items.append(
                (
                    remainder,
                    ForecastCashflowItem(
                        date=current_date,
                        amount=float(remainder),
                        label=uncategorized_label,
                        category=uncategorized_label,
                        source="uncategorized",
                        type=_cashflow_type(remainder),
                        confidence=float(DEFAULT_UNCATEGORIZED_CONFIDENCE),
                        direction=_cashflow_direction(remainder),
                        metadata={"reason": "delta-remainder"},
                    ),
                )
            )

        cashflows.extend(item for _, item in day_items)

    if adjustments:
        cashflows.extend(_build_adjustment_cashflows(adjustments, timeline_dates))

    return cashflows


def _build_adjustment_cashflows(
    adjustments: Sequence[Mapping[str, Any]], timeline_dates: Sequence[date]
) -> list[ForecastCashflowItem]:
    """Return cashflow items derived from adjustments."""
    cashflows: list[ForecastCashflowItem] = []
    for adjustment in adjustments:
        amount = _to_decimal(_read_entry_value(adjustment, "amount", 0))
        if amount == 0:
            continue
        label = str(_read_entry_value(adjustment, "label", "Adjustment"))
        adjustment_type = _read_entry_value(adjustment, "adjustment_type", "manual")
        reason = _read_entry_value(adjustment, "reason")
        adjustment_id = _read_entry_value(adjustment, "adjustment_id")
        frequency = _normalize_frequency(_read_entry_value(adjustment, "frequency"))
        start_date = _parse_date(
            _read_entry_value(adjustment, "date")
            or _read_entry_value(adjustment, "start_date"),
            fallback=timeline_dates[0],
        )
        confidence = float(
            _read_entry_value(adjustment, "confidence", DEFAULT_ADJUSTMENT_CONFIDENCE)
        )

        for current_date in timeline_dates:
            if _matches_frequency(current_date, start_date, frequency):
                cashflows.append(
                    ForecastCashflowItem(
                        date=current_date,
                        amount=float(amount),
                        label=label,
                        category="Adjustment",
                        source="adjustment",
                        type=_cashflow_type(amount),
                        confidence=confidence,
                        direction=_cashflow_direction(amount),
                        metadata={
                            "adjustment_type": adjustment_type,
                            "adjustment_id": adjustment_id,
                            "reason": reason,
                            "frequency": frequency or "one-time",
                        },
                    )
                )
                if frequency is None:
                    break

    return cashflows


def apply_adjustments(
    baseline_timeline: Sequence[ForecastTimelinePoint],
    adjustments: Sequence[Mapping[str, Any]] | None,
) -> list[ForecastTimelinePoint]:
    """Apply one-time or recurring adjustments to a baseline forecast timeline.

    Args:
        baseline_timeline: Baseline projection timeline to adjust.
        adjustments: Adjustment entries with dates, amounts, and optional frequency.

    Returns:
        New list of timeline points with adjustments applied.
    """
    if not baseline_timeline:
        return []

    timeline = list(baseline_timeline)
    timeline_dates = [
        _parse_date(point.date, fallback=date.today()) for point in timeline
    ]
    adjustment_schedule = _build_adjustment_schedule(adjustments or [], timeline_dates)
    running_adjustment = Decimal("0")
    adjusted_points: list[ForecastTimelinePoint] = []

    for point, current_date in zip(timeline, timeline_dates):
        adjustment_delta = adjustment_schedule.get(current_date, Decimal("0"))
        running_adjustment += adjustment_delta

        base_balance = _to_decimal(point.forecast_balance)
        adjusted_balance = base_balance + running_adjustment
        actual_balance = point.actual_balance
        updated_delta = None
        if actual_balance is not None:
            updated_delta = float(adjusted_balance - _to_decimal(actual_balance))

        metadata = dict(point.metadata or {})
        metadata["baseline_balance"] = float(base_balance)
        metadata["adjustment_total"] = float(running_adjustment)

        adjusted_points.append(
            ForecastTimelinePoint(
                date=point.date,
                label=point.label,
                forecast_balance=float(adjusted_balance),
                actual_balance=actual_balance,
                delta=updated_delta if updated_delta is not None else point.delta,
                metadata=metadata,
            )
        )

    return adjusted_points


def _build_adjustment_schedule(
    adjustments: Sequence[Mapping[str, Any]],
    timeline_dates: Sequence[date],
) -> dict[date, Decimal]:
    """Build per-date adjustment totals."""
    schedule: dict[date, Decimal] = {day: Decimal("0") for day in timeline_dates}
    if not timeline_dates:
        return schedule

    for adjustment in adjustments:
        amount = _to_decimal(_read_entry_value(adjustment, "amount", 0))
        if amount == 0:
            continue
        frequency = _normalize_frequency(_read_entry_value(adjustment, "frequency"))
        start_date = _parse_date(
            _read_entry_value(adjustment, "date")
            or _read_entry_value(adjustment, "start_date"),
            fallback=timeline_dates[0],
        )

        for current_date in timeline_dates:
            if _matches_frequency(current_date, start_date, frequency):
                schedule[current_date] += amount
                if frequency is None:
                    break

    return schedule


def project_balances(
    user_id: int,
    start_date: DateLike,
    horizon_days: int,
    latest_snapshots: Sequence[Mapping[str, Any]],
    historical_aggregates: Sequence[Mapping[str, Any]],
) -> list[ForecastTimelinePoint]:
    """Project a daily balance timeline using average inflows/outflows.

    Args:
        user_id: Identifier for the user owning the balances.
        start_date: First date included in the projection.
        horizon_days: Number of days to project, including the start date.
        latest_snapshots: Latest balance snapshots for the user. Each mapping should include a
            ``balance`` field and ideally an ``account_id`` and ``date`` for deterministic
            selection.
        historical_aggregates: Historical daily aggregates with inflow/outflow totals. Each mapping
            should include a ``date`` plus inflow/outflow fields such as ``inflow``/``outflow`` or
            ``income``/``expense``.

    Returns:
        A list of :class:`ForecastTimelinePoint` entries ordered by date.
    """

    anchor_date = _parse_date(start_date, fallback=date.today())
    horizon_days = max(int(horizon_days), 0)

    # Select the latest snapshot per account for the requested user to anchor the forecast.
    latest_by_account: dict[str, tuple[date, Decimal]] = {}
    for index, snapshot in enumerate(latest_snapshots):
        snapshot_user = snapshot.get("user_id")
        if snapshot_user is not None and snapshot_user != user_id:
            continue

        account_id = str(snapshot.get("account_id", snapshot.get("id", index)))
        snapshot_date = _parse_date(
            snapshot.get("date") or snapshot.get("as_of"),
            fallback=anchor_date,
        )
        balance = _to_decimal(snapshot.get("balance"))

        existing = latest_by_account.get(account_id)
        if existing is None:
            latest_by_account[account_id] = (snapshot_date, balance)
            continue

        existing_date, existing_balance = existing
        if snapshot_date > existing_date or (
            snapshot_date == existing_date and balance > existing_balance
        ):
            latest_by_account[account_id] = (snapshot_date, balance)

    starting_balance = sum(
        (balance for _, balance in latest_by_account.values()), Decimal("0")
    )

    # Compute the average inflow/outflow per day from historical aggregates.
    inflow_keys = (
        "inflow",
        "inflows",
        "income",
        "credit",
        "total_inflow",
        "inflow_total",
    )
    outflow_keys = (
        "outflow",
        "outflows",
        "expense",
        "debit",
        "total_outflow",
        "outflow_total",
    )
    net_keys = ("net", "net_change", "net_total")

    total_inflow = Decimal("0")
    total_outflow = Decimal("0")
    aggregate_dates: set[date] = set()

    for aggregate in historical_aggregates:
        aggregate_date = aggregate.get("date")
        if aggregate_date is not None:
            aggregate_dates.add(_parse_date(aggregate_date, fallback=anchor_date))

        inflow = _extract_amount(aggregate, inflow_keys)
        outflow = _extract_amount(aggregate, outflow_keys)

        if inflow == Decimal("0") and outflow == Decimal("0"):
            net_amount = _extract_amount(aggregate, net_keys)
            if net_amount > 0:
                inflow = net_amount
            elif net_amount < 0:
                outflow = abs(net_amount)

        total_inflow += inflow
        total_outflow += outflow

    day_count = len(aggregate_dates) if aggregate_dates else len(historical_aggregates)
    if day_count <= 0:
        average_inflow = Decimal("0")
        average_outflow = Decimal("0")
    else:
        average_inflow = total_inflow / Decimal(day_count)
        average_outflow = total_outflow / Decimal(day_count)

    # Build the projection by applying the average daily net change to the latest balance.
    points: list[ForecastTimelinePoint] = []
    current_balance = starting_balance
    for day_offset in range(horizon_days):
        current_date = anchor_date + timedelta(days=day_offset)

        # Apply the daily net change before recording the day's projected balance.
        current_balance += average_inflow - average_outflow

        points.append(
            ForecastTimelinePoint(
                date=current_date,
                label=current_date.isoformat(),
                forecast_balance=float(current_balance),
                metadata={
                    "average_inflow": float(average_inflow),
                    "average_outflow": float(average_outflow),
                    "starting_balance": float(starting_balance),
                },
            )
        )

    return points

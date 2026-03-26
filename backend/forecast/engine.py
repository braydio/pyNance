"""Forecast projection helpers for balance timelines."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from .models import (
    DateLike,
    ForecastAdjustment,
    ForecastAspectSeries,
    ForecastCashflowItem,
    ForecastResult,
    ForecastSeriesPoint,
    ForecastSummary,
    ForecastTimelinePoint,
)

DEFAULT_CATEGORY_CONFIDENCE = Decimal("0.6")
DEFAULT_RECURRING_CONFIDENCE = Decimal("0.85")
DEFAULT_UNCATEGORIZED_CONFIDENCE = Decimal("0.3")
DEFAULT_ADJUSTMENT_CONFIDENCE = Decimal("0.95")
DEBT_SERIES_TOTAL_KEY = "debt_totals"
DEBT_SERIES_INTEREST_KEY = "debt_interest"
DEBT_SERIES_NEW_SPENDING_KEY = "debt_new_spending"
LIABILITY_ACCOUNT_TYPE_TOKENS = {
    "credit",
    "credit card",
    "loan",
    "liability",
    "line of credit",
    "mortgage",
    "student",
    "debt",
}


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


def _normalize_graph_mode(value: Any) -> str:
    """Normalize graph mode values used by frontend chart switching."""
    normalized = str(value or "combined").strip().lower()
    if normalized not in {"combined", "forecast", "historical"}:
        return "combined"
    return normalized


def _normalize_window(value: Any) -> int:
    """Normalize moving average window to one of the supported API values."""
    allowed = {7, 30, 60, 90}
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 30
    return parsed if parsed in allowed else 30


def _is_liability_account_type(raw_account_type: object) -> bool:
    """Return ``True`` when an account type should be treated as a liability."""
    normalized = str(raw_account_type or "").strip().lower().replace("_", " ")
    if not normalized:
        return False

    normalized = normalized.replace("-", " ").replace("/", " ")
    return any(token in normalized for token in LIABILITY_ACCOUNT_TYPE_TOKENS)


def _matches_frequency(current_date: date, start_date: date, frequency: str | None) -> bool:
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


def _normalize_debt_component(value: Any) -> str | None:
    """Normalize debt component labels into stable forecast series keys."""
    normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if normalized in {"interest", DEBT_SERIES_INTEREST_KEY}:
        return DEBT_SERIES_INTEREST_KEY
    if normalized in {"new_spending", "principal", "spending", DEBT_SERIES_NEW_SPENDING_KEY}:
        return DEBT_SERIES_NEW_SPENDING_KEY
    return None


def _debt_component_from_entry(entry: Mapping[str, Any] | ForecastCashflowItem | Any) -> str | None:
    """Read normalized debt attribution metadata from an entry."""
    metadata = _read_entry_value(entry, "metadata", {}) or {}
    if isinstance(metadata, Mapping):
        for key in ("debt_series_key", "debt_component", "debt_contribution_type"):
            component = _normalize_debt_component(metadata.get(key))
            if component:
                return component

    for key in ("debt_series_key", "debt_component", "debt_contribution_type"):
        component = _normalize_debt_component(_read_entry_value(entry, key))
        if component:
            return component

    label = str(_read_entry_value(entry, "label", "")).strip().lower()
    adjustment_type = str(_read_entry_value(entry, "adjustment_type", "")).strip().lower()
    if "debt" in label or "liability" in label or "debt" in adjustment_type:
        return DEBT_SERIES_NEW_SPENDING_KEY
    return None


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


def _starting_balance(timeline: Sequence[ForecastTimelinePoint]) -> Decimal:
    """Return the starting balance for a timeline."""
    if not timeline:
        return Decimal("0")

    first_point = timeline[0]
    first_balance = _to_decimal(first_point.forecast_balance)
    metadata = first_point.metadata or {}
    if "starting_balance" in metadata:
        return _to_decimal(metadata.get("starting_balance"))
    if "average_inflow" in metadata and "average_outflow" in metadata:
        average_inflow = _to_decimal(metadata.get("average_inflow"))
        average_outflow = _to_decimal(metadata.get("average_outflow"))
        return first_balance - (average_inflow - average_outflow)
    return first_balance


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
        label = str(entry.get("category") or entry.get("label") or entry.get("name") or "Uncategorized")
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

        label = str(entry.get("label") or entry.get("merchant") or entry.get("description") or "Recurring")
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


def _scaled_category_items(remaining: Decimal, category_sources: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Scale category averages to match the remaining delta."""
    if not category_sources or remaining == 0:
        return []

    category_total = sum((_to_decimal(source.get("amount")) for source in category_sources), Decimal("0"))
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

    for point, (current_date, delta) in zip(timeline, daily_deltas):
        day_items: list[tuple[Decimal, ForecastCashflowItem]] = []
        recurring_items = recurring_by_date.get(current_date, [])
        recurring_total = sum((_to_decimal(item.get("amount")) for item in recurring_items), Decimal("0"))

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
                        confidence=float(entry.get("confidence", DEFAULT_RECURRING_CONFIDENCE)),
                        direction=_cashflow_direction(amount),
                        metadata=entry.get("metadata", {}),
                    ),
                )
            )

        debt_component_total = Decimal("0")
        for debt_amount, debt_item in _build_baseline_debt_cashflows(current_date, point.metadata or {}):
            debt_component_total += debt_amount
            day_items.append((debt_amount, debt_item))

        remaining = delta - recurring_total - debt_component_total
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
                        confidence=float(entry.get("confidence", DEFAULT_CATEGORY_CONFIDENCE)),
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


def _build_baseline_debt_cashflows(
    current_date: date,
    point_metadata: Mapping[str, Any],
) -> list[tuple[Decimal, ForecastCashflowItem]]:
    """Build explicit cashflow rows for projected debt growth components."""
    component_configs = (
        (DEBT_SERIES_INTEREST_KEY, "Debt interest accrual", point_metadata.get("average_debt_interest")),
        (DEBT_SERIES_NEW_SPENDING_KEY, "Debt new spending", point_metadata.get("average_debt_new_spending")),
    )
    items: list[tuple[Decimal, ForecastCashflowItem]] = []
    for component_key, label, raw_amount in component_configs:
        growth_amount = _to_decimal(raw_amount)
        if growth_amount <= 0:
            continue

        signed_amount = -growth_amount
        items.append(
            (
                signed_amount,
                ForecastCashflowItem(
                    date=current_date,
                    amount=float(signed_amount),
                    label=label,
                    category="Debt",
                    source="historical_debt_average",
                    type="expense",
                    confidence=float(DEFAULT_CATEGORY_CONFIDENCE),
                    direction="outflow",
                    metadata={
                        "debt_component": component_key,
                        "debt_series_key": component_key,
                        "semantic_type": "debt_contribution",
                        "affects_debt_total": True,
                        "debt_growth_amount": float(growth_amount),
                    },
                ),
            )
        )
    return items


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
            _read_entry_value(adjustment, "date") or _read_entry_value(adjustment, "start_date"),
            fallback=timeline_dates[0],
        )
        confidence = float(_read_entry_value(adjustment, "confidence", DEFAULT_ADJUSTMENT_CONFIDENCE))
        debt_component = _debt_component_from_entry(adjustment)

        for current_date in timeline_dates:
            if _matches_frequency(current_date, start_date, frequency):
                metadata = {
                    "adjustment_type": adjustment_type,
                    "adjustment_id": adjustment_id,
                    "reason": reason,
                    "frequency": frequency or "one-time",
                }
                if debt_component:
                    metadata.update(
                        {
                            "debt_component": debt_component,
                            "debt_series_key": debt_component,
                            "semantic_type": "debt_contribution",
                            "affects_debt_total": True,
                            "debt_growth_amount": float(abs(amount)),
                        }
                    )

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
                        metadata=metadata,
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
    timeline_dates = [_parse_date(point.date, fallback=date.today()) for point in timeline]
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


def compute_summary(
    timeline: Sequence[ForecastTimelinePoint],
) -> ForecastSummary:
    """Compute summary metrics for a forecast timeline.

    Args:
        timeline: Forecast timeline points to summarize.

    Returns:
        Summary metrics including balances, min/max values, and depletion date.
    """
    if not timeline:
        today = date.today()
        return ForecastSummary(
            start_date=today,
            end_date=today,
            starting_balance=0.0,
            ending_balance=0.0,
            net_change=0.0,
            total_inflows=0.0,
            total_outflows=0.0,
            average_daily_change=0.0,
            min_balance=0.0,
            max_balance=0.0,
            depletion_date=None,
            metadata={"reason": "empty-timeline"},
        )

    start_date = _parse_date(timeline[0].date, fallback=date.today())
    end_date = _parse_date(timeline[-1].date, fallback=start_date)
    starting_balance = _starting_balance(timeline)
    ending_balance = _to_decimal(timeline[-1].forecast_balance)

    balances = [starting_balance] + [_to_decimal(point.forecast_balance) for point in timeline]
    min_balance = min(balances)
    max_balance = max(balances)

    net_change = ending_balance - starting_balance
    daily_deltas = _daily_deltas(timeline)
    total_inflows = sum((delta for _, delta in daily_deltas if delta > 0), Decimal("0"))
    total_outflows = sum((-delta for _, delta in daily_deltas if delta < 0), Decimal("0"))
    average_daily_change = net_change / Decimal(len(daily_deltas)) if daily_deltas else Decimal("0")

    depletion_date: date | None = None
    if starting_balance <= 0:
        depletion_date = start_date
    else:
        for point in timeline:
            point_balance = _to_decimal(point.forecast_balance)
            if point_balance <= 0:
                depletion_date = _parse_date(point.date, fallback=start_date)
                break

    return ForecastSummary(
        start_date=start_date,
        end_date=end_date,
        starting_balance=float(starting_balance),
        ending_balance=float(ending_balance),
        net_change=float(net_change),
        total_inflows=float(total_inflows),
        total_outflows=float(total_outflows),
        average_daily_change=float(average_daily_change),
        min_balance=float(min_balance),
        max_balance=float(max_balance),
        depletion_date=depletion_date,
    )


def _build_adjustment_models(
    adjustments: Sequence[Mapping[str, Any]] | None,
) -> list[ForecastAdjustment]:
    """Normalize adjustment payloads into forecast adjustment models."""
    models: list[ForecastAdjustment] = []
    for adjustment in adjustments or []:
        amount = _to_decimal(_read_entry_value(adjustment, "amount", 0))
        if amount == 0:
            continue
        label = str(_read_entry_value(adjustment, "label", "Adjustment"))
        adjustment_type = str(
            _read_entry_value(
                adjustment,
                "adjustment_type",
                _read_entry_value(adjustment, "type", "manual"),
            )
        )
        adjustment_date = _read_entry_value(adjustment, "date") or _read_entry_value(adjustment, "start_date")
        if adjustment_date is None:
            adjustment_date = date.today()
        reason = _read_entry_value(adjustment, "reason")
        adjustment_id = _read_entry_value(adjustment, "adjustment_id", _read_entry_value(adjustment, "id"))
        metadata: dict[str, Any] = dict(_read_entry_value(adjustment, "metadata", {}) or {})
        frequency = _read_entry_value(adjustment, "frequency")
        if frequency:
            metadata["frequency"] = frequency
        debt_component = _debt_component_from_entry(adjustment)
        if debt_component:
            metadata.setdefault("debt_component", debt_component)
            metadata.setdefault("debt_series_key", debt_component)
            metadata.setdefault("semantic_type", "debt_contribution")

        models.append(
            ForecastAdjustment(
                label=label,
                amount=float(amount),
                date=adjustment_date,
                adjustment_type=adjustment_type,
                reason=reason,
                adjustment_id=adjustment_id,
                metadata=metadata,
            )
        )
    return models


def _build_daily_series(
    *,
    series_id: str,
    label: str,
    dates: Sequence[date],
    values_by_date: Mapping[date, Decimal],
    metadata: Mapping[str, Any] | None = None,
) -> ForecastAspectSeries:
    """Build a named daily series from per-date decimal values."""
    return ForecastAspectSeries(
        id=series_id,
        label=label,
        points=[
            ForecastSeriesPoint(
                date=current_date,
                label=current_date.isoformat(),
                value=float(values_by_date.get(current_date, Decimal("0"))),
            )
            for current_date in dates
        ],
        metadata=dict(metadata or {}),
    )


def _manual_adjustment_values_by_date(
    adjustments: Sequence[Mapping[str, Any]] | None,
    timeline_dates: Sequence[date],
) -> dict[date, Decimal]:
    """Return per-day totals for manual user-entered adjustments."""
    manual_adjustments = [
        adjustment
        for adjustment in adjustments or []
        if not str(_read_entry_value(adjustment, "adjustment_type", "manual")).strip().lower().startswith("auto")
    ]
    return _build_adjustment_schedule(manual_adjustments, timeline_dates)


def _realized_income_values_by_date(
    historical_aggregates: Sequence[Mapping[str, Any]],
    dates: Sequence[date],
) -> dict[date, Decimal]:
    """Return realized income totals keyed by the supplied historical dates."""
    income_by_date: dict[date, Decimal] = {current_date: Decimal("0") for current_date in dates}
    for entry in historical_aggregates:
        current_date = _parse_date(entry.get("date"), fallback=date.today())
        if current_date not in income_by_date:
            continue
        income_by_date[current_date] += _extract_amount(entry, ("inflow", "income", "credit", "average_inflow"))
    return income_by_date


def _spending_values_by_date(
    cashflows: Sequence[ForecastCashflowItem],
    timeline_dates: Sequence[date],
) -> dict[date, Decimal]:
    """Return realized/projected spending totals from cashflows as negative values."""
    spending_by_date: dict[date, Decimal] = {current_date: Decimal("0") for current_date in timeline_dates}
    for cashflow in cashflows:
        current_date = _parse_date(cashflow.date, fallback=timeline_dates[0] if timeline_dates else date.today())
        if current_date not in spending_by_date:
            continue
        if str(cashflow.source).strip().lower() == "adjustment":
            continue
        amount = _to_decimal(cashflow.amount)
        if amount < 0:
            spending_by_date[current_date] += amount
    return spending_by_date


def _initial_debt_total(latest_snapshots: Sequence[Mapping[str, Any]]) -> Decimal:
    """Return the total liability balance present in the latest snapshots."""
    debt_total = Decimal("0")
    for snapshot in latest_snapshots:
        balance = _to_decimal(snapshot.get("balance"))
        if _is_liability_account_type(snapshot.get("account_type")):
            debt_total += abs(balance)
    return debt_total


def _baseline_debt_component_values_by_date(
    timeline: Sequence[ForecastTimelinePoint],
) -> dict[str, dict[date, Decimal]]:
    """Return projected baseline debt growth values keyed by component."""
    component_map = {
        DEBT_SERIES_INTEREST_KEY: {},
        DEBT_SERIES_NEW_SPENDING_KEY: {},
    }
    for point in timeline:
        current_date = _parse_date(point.date, fallback=date.today())
        metadata = point.metadata or {}
        component_map[DEBT_SERIES_INTEREST_KEY][current_date] = _to_decimal(metadata.get("average_debt_interest"))
        component_map[DEBT_SERIES_NEW_SPENDING_KEY][current_date] = _to_decimal(
            metadata.get("average_debt_new_spending")
        )
    return component_map


def _adjustment_debt_component_values_by_date(
    adjustments: Sequence[Mapping[str, Any]] | None,
    timeline_dates: Sequence[date],
) -> dict[str, dict[date, Decimal]]:
    """Return per-day debt component deltas contributed by adjustments."""
    component_map = {
        DEBT_SERIES_INTEREST_KEY: {current_date: Decimal("0") for current_date in timeline_dates},
        DEBT_SERIES_NEW_SPENDING_KEY: {current_date: Decimal("0") for current_date in timeline_dates},
    }
    for adjustment in adjustments or []:
        component = _debt_component_from_entry(adjustment)
        if not component:
            continue

        scheduled_values = _build_adjustment_schedule([adjustment], timeline_dates)
        for current_date, signed_balance_delta in scheduled_values.items():
            component_map[component][current_date] += -signed_balance_delta

    return component_map


def _debt_series_values(
    *,
    latest_snapshots: Sequence[Mapping[str, Any]],
    baseline_timeline: Sequence[ForecastTimelinePoint],
    adjustments: Sequence[Mapping[str, Any]] | None,
    timeline_dates: Sequence[date],
) -> dict[str, dict[date, Decimal]]:
    """Build debt balance and component series for the forecast horizon."""
    baseline_components = _baseline_debt_component_values_by_date(baseline_timeline)
    adjustment_components = _adjustment_debt_component_values_by_date(adjustments, timeline_dates)

    interest_values = {
        current_date: baseline_components[DEBT_SERIES_INTEREST_KEY].get(current_date, Decimal("0"))
        + adjustment_components[DEBT_SERIES_INTEREST_KEY].get(current_date, Decimal("0"))
        for current_date in timeline_dates
    }
    new_spending_values = {
        current_date: baseline_components[DEBT_SERIES_NEW_SPENDING_KEY].get(current_date, Decimal("0"))
        + adjustment_components[DEBT_SERIES_NEW_SPENDING_KEY].get(current_date, Decimal("0"))
        for current_date in timeline_dates
    }

    running_total = _initial_debt_total(latest_snapshots)
    total_values: dict[date, Decimal] = {}
    for current_date in timeline_dates:
        running_total += interest_values.get(current_date, Decimal("0"))
        running_total += new_spending_values.get(current_date, Decimal("0"))
        total_values[current_date] = running_total

    return {
        DEBT_SERIES_TOTAL_KEY: total_values,
        DEBT_SERIES_INTEREST_KEY: interest_values,
        DEBT_SERIES_NEW_SPENDING_KEY: new_spending_values,
    }


def _build_forecast_series(
    *,
    historical_aggregates: Sequence[Mapping[str, Any]],
    historical_dates: Sequence[date],
    adjustments: Sequence[Mapping[str, Any]] | None,
    baseline_timeline: Sequence[ForecastTimelinePoint],
    timeline_dates: Sequence[date],
    cashflows: Sequence[ForecastCashflowItem],
    latest_snapshots: Sequence[Mapping[str, Any]],
) -> dict[str, ForecastAspectSeries]:
    """Build typed aspect series for frontend charting and summaries."""
    debt_values = _debt_series_values(
        latest_snapshots=latest_snapshots,
        baseline_timeline=baseline_timeline,
        adjustments=adjustments,
        timeline_dates=timeline_dates,
    )
    return {
        "realized_income": _build_daily_series(
            series_id="realized_income",
            label="Realized income used for auto-calculation",
            dates=historical_dates,
            values_by_date=_realized_income_values_by_date(historical_aggregates, historical_dates),
            metadata={"timeframe": "historical", "source": "historical_aggregates"},
        ),
        "manual_adjustments": _build_daily_series(
            series_id="manual_adjustments",
            label="Manual adjustments",
            dates=timeline_dates,
            values_by_date=_manual_adjustment_values_by_date(adjustments, timeline_dates),
            metadata={"timeframe": "forecast", "source": "adjustments"},
        ),
        "spending": _build_daily_series(
            series_id="spending",
            label="Spending",
            dates=timeline_dates,
            values_by_date=_spending_values_by_date(cashflows, timeline_dates),
            metadata={"timeframe": "forecast", "source": "cashflows"},
        ),
        DEBT_SERIES_TOTAL_KEY: _build_daily_series(
            series_id=DEBT_SERIES_TOTAL_KEY,
            label="Total debt",
            dates=timeline_dates,
            values_by_date=debt_values[DEBT_SERIES_TOTAL_KEY],
            metadata={"timeframe": "forecast", "source": "debt_projection", "value_mode": "balance"},
        ),
        DEBT_SERIES_INTEREST_KEY: _build_daily_series(
            series_id=DEBT_SERIES_INTEREST_KEY,
            label="Debt interest accrual",
            dates=timeline_dates,
            values_by_date=debt_values[DEBT_SERIES_INTEREST_KEY],
            metadata={"timeframe": "forecast", "source": "debt_projection", "value_mode": "daily_change"},
        ),
        DEBT_SERIES_NEW_SPENDING_KEY: _build_daily_series(
            series_id=DEBT_SERIES_NEW_SPENDING_KEY,
            label="Debt new spending",
            dates=timeline_dates,
            values_by_date=debt_values[DEBT_SERIES_NEW_SPENDING_KEY],
            metadata={"timeframe": "forecast", "source": "debt_projection", "value_mode": "daily_change"},
        ),
    }


def compute_forecast(
    *,
    user_id: int,
    start_date: DateLike,
    horizon_days: int,
    latest_snapshots: Sequence[Mapping[str, Any]],
    historical_aggregates: Sequence[Mapping[str, Any]],
    category_averages: Sequence[Mapping[str, Any]] | None = None,
    recurring_sources: Sequence[Mapping[str, Any]] | None = None,
    adjustments: Sequence[Mapping[str, Any]] | None = None,
    moving_average_window: int = 30,
    normalize: bool = False,
    graph_mode: str = "combined",
    currency: str = "USD",
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute a full forecast payload for API responses.

    Args:
        user_id: Identifier for the forecast owner.
        start_date: First date included in the projection.
        horizon_days: Number of days to project.
        latest_snapshots: Latest per-account balance snapshots.
        historical_aggregates: Historical daily inflow/outflow aggregates.
        category_averages: Optional category averages for cashflow labels.
        recurring_sources: Optional recurring transaction labels.
        adjustments: Optional manual or automated adjustments.
        moving_average_window: Number of historical days to average (7/30/60/90).
        normalize: Whether to normalize historical amounts before projection.
        graph_mode: Chart mode hint (combined, forecast, historical).
        currency: ISO currency code for summary display.
        metadata: Optional metadata to attach to the forecast result.

    Returns:
        Fully serialized forecast payload.
    """
    window = _normalize_window(moving_average_window)
    sorted_aggregates = sorted(
        historical_aggregates,
        key=lambda item: _parse_date(item.get("date"), fallback=date.today()),
    )
    historical_window = sorted_aggregates[-window:] if sorted_aggregates else []

    normalization_factor = Decimal("1")
    normalized_aggregates = historical_window
    if normalize and historical_window:
        magnitudes = [
            abs(_extract_amount(item, ("inflow", "income", "credit")))
            + abs(_extract_amount(item, ("outflow", "expense", "debit")))
            for item in historical_window
        ]
        non_zero = [value for value in magnitudes if value > 0]
        if non_zero:
            normalization_factor = max(non_zero)
            normalized_aggregates = []
            for item in historical_window:
                normalized_aggregates.append(
                    {
                        **item,
                        "inflow": float(_extract_amount(item, ("inflow", "income", "credit")) / normalization_factor),
                        "outflow": float(_extract_amount(item, ("outflow", "expense", "debit")) / normalization_factor),
                        DEBT_SERIES_INTEREST_KEY: float(
                            _extract_amount(item, (DEBT_SERIES_INTEREST_KEY,)) / normalization_factor
                        ),
                        DEBT_SERIES_NEW_SPENDING_KEY: float(
                            _extract_amount(item, (DEBT_SERIES_NEW_SPENDING_KEY,)) / normalization_factor
                        ),
                    }
                )

    baseline_timeline = project_balances(
        user_id=user_id,
        start_date=start_date,
        horizon_days=horizon_days,
        latest_snapshots=latest_snapshots,
        historical_aggregates=normalized_aggregates,
    )
    if normalize and normalization_factor != Decimal("1"):
        denormalized_timeline: list[ForecastTimelinePoint] = []
        for point in baseline_timeline:
            point_metadata = dict(point.metadata or {})
            point_metadata["normalization_factor"] = float(normalization_factor)
            denormalized_timeline.append(
                ForecastTimelinePoint(
                    date=point.date,
                    label=point.label,
                    forecast_balance=float(_to_decimal(point.forecast_balance) * normalization_factor),
                    actual_balance=point.actual_balance,
                    delta=point.delta,
                    metadata=point_metadata,
                )
            )
        baseline_timeline = denormalized_timeline

    adjusted_timeline = apply_adjustments(baseline_timeline, adjustments)
    cashflows = build_cashflow_items(
        baseline_timeline,
        category_averages=category_averages,
        recurring_sources=recurring_sources,
        adjustments=adjustments,
    )
    historical_dates = [_parse_date(item.get("date"), fallback=date.today()) for item in historical_window]
    timeline_dates = [_parse_date(point.date, fallback=date.today()) for point in adjusted_timeline]
    series = _build_forecast_series(
        historical_aggregates=historical_window,
        historical_dates=historical_dates,
        adjustments=adjustments,
        baseline_timeline=baseline_timeline,
        timeline_dates=timeline_dates,
        cashflows=cashflows,
        latest_snapshots=latest_snapshots,
    )
    summary = compute_summary(adjusted_timeline)
    summary.currency = currency
    projected_amount = summary.ending_balance
    projected_change = summary.net_change
    projected_change_percent = (projected_change / summary.starting_balance) * 100 if summary.starting_balance else 0.0

    realized_history: list[dict[str, object]] = []
    metadata_map = dict(metadata or {})
    provided_realized_history = metadata_map.get("realized_history")
    if isinstance(provided_realized_history, list):
        normalized_points: list[tuple[date, dict[str, object]]] = []
        for point in provided_realized_history:
            if not isinstance(point, Mapping):
                continue
            realized_date = _parse_date(point.get("date"), fallback=date.today())
            normalized_points.append(
                (
                    realized_date,
                    {
                        "date": realized_date.isoformat(),
                        "label": str(point.get("label") or realized_date.isoformat()),
                        "balance": float(
                            _to_decimal(point.get("balance") or point.get("value") or point.get("amount"))
                        ),
                    },
                )
            )
        normalized_points.sort(key=lambda item: item[0])
        realized_history = [item[1] for item in normalized_points]

    if not realized_history and historical_window:
        anchor_date = _parse_date(start_date, fallback=date.today())
        running_history_balance = Decimal(str(summary.starting_balance))
        daily_net_by_date: dict[date, Decimal] = {}
        for item in historical_window:
            realized_date = _parse_date(item.get("date"), fallback=anchor_date)
            daily_net_by_date[realized_date] = (
                daily_net_by_date.get(realized_date, Decimal("0"))
                + _extract_amount(item, ("inflow", "income", "credit"))
                - _extract_amount(item, ("outflow", "expense", "debit"))
            )

        oldest_date = min(daily_net_by_date)
        realized_history_desc: list[dict[str, object]] = []
        current_date = anchor_date
        while current_date >= oldest_date:
            iso_date = current_date.isoformat()
            realized_history_desc.append(
                {
                    "date": iso_date,
                    "label": iso_date,
                    "balance": float(running_history_balance),
                }
            )
            running_history_balance -= daily_net_by_date.get(current_date, Decimal("0"))
            current_date -= timedelta(days=1)

        realized_history_desc.reverse()
        realized_history = realized_history_desc

    normalized_graph_mode = _normalize_graph_mode(graph_mode)
    summary_metadata = dict(summary.metadata or {})
    summary_metadata.update(
        {
            "moving_average_window": window,
            "normalize": normalize,
            "graph_mode": normalized_graph_mode,
            "normalization_factor": float(normalization_factor),
            "projected_amount": projected_amount,
            "projected_change": projected_change,
            "projected_change_percent": projected_change_percent,
            "realized_history": realized_history,
        }
    )
    summary.metadata = summary_metadata

    result = ForecastResult(
        timeline=adjusted_timeline,
        summary=summary,
        cashflows=cashflows,
        adjustments=_build_adjustment_models(adjustments),
        series=series,
        metadata={
            **metadata_map,
            "moving_average_window": window,
            "normalize": normalize,
            "graph_mode": normalized_graph_mode,
            "normalization_factor": float(normalization_factor),
            "projected_amount": projected_amount,
            "projected_change": projected_change,
            "projected_change_percent": projected_change_percent,
            "realized_history": realized_history,
        },
    )
    return result.to_dict()


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

        distribution = str(_read_entry_value(adjustment, "distribution", "single")).strip().lower()
        if distribution in {"spread", "distributed"}:
            range_start = _parse_date(
                _read_entry_value(adjustment, "range_start") or _read_entry_value(adjustment, "date"),
                fallback=timeline_dates[0],
            )
            range_end = _parse_date(
                _read_entry_value(adjustment, "range_end") or _read_entry_value(adjustment, "date"),
                fallback=range_start,
            )
            if range_end < range_start:
                range_start, range_end = range_end, range_start
            selected_dates = [
                current_date for current_date in timeline_dates if range_start <= current_date <= range_end
            ]
            if selected_dates:
                per_day_amount = amount / Decimal(len(selected_dates))
                for current_date in selected_dates:
                    schedule[current_date] += per_day_amount
            continue

        frequency = _normalize_frequency(_read_entry_value(adjustment, "frequency"))
        start_date = _parse_date(
            _read_entry_value(adjustment, "date") or _read_entry_value(adjustment, "start_date"),
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
        if snapshot_date > existing_date or (snapshot_date == existing_date and balance > existing_balance):
            latest_by_account[account_id] = (snapshot_date, balance)

    starting_balance = sum((balance for _, balance in latest_by_account.values()), Decimal("0"))

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
    total_debt_interest = Decimal("0")
    total_debt_new_spending = Decimal("0")
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
        total_debt_interest += _extract_amount(aggregate, (DEBT_SERIES_INTEREST_KEY,))
        total_debt_new_spending += _extract_amount(aggregate, (DEBT_SERIES_NEW_SPENDING_KEY,))

    day_count = len(aggregate_dates) if aggregate_dates else len(historical_aggregates)
    if day_count <= 0:
        average_inflow = Decimal("0")
        average_outflow = Decimal("0")
        average_debt_interest = Decimal("0")
        average_debt_new_spending = Decimal("0")
    else:
        average_inflow = total_inflow / Decimal(day_count)
        average_outflow = total_outflow / Decimal(day_count)
        average_debt_interest = total_debt_interest / Decimal(day_count)
        average_debt_new_spending = total_debt_new_spending / Decimal(day_count)

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
                    "average_debt_interest": float(average_debt_interest),
                    "average_debt_new_spending": float(average_debt_new_spending),
                    "starting_balance": float(starting_balance),
                },
            )
        )

    return points

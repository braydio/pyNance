"""Typed models for forecast responses.

These dataclasses define the serialized shape of forecast responses delivered to the
frontend, including the timeline, summary, supporting cashflow details, and
aspect-specific series keyed by stable chart identifiers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal, Mapping, Optional, Sequence, TypeAlias

DateLike = str | date | datetime
ForecastSeriesId: TypeAlias = Literal[
    "realized_income",
    "manual_adjustments",
    "spending",
    "debt_totals",
]


def _serialize_value(value: Any) -> Any:
    """Normalize values into JSON-serializable structures."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, Mapping):
        return {key: _serialize_value(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_serialize_value(item) for item in value]
    return value


@dataclass
class ForecastTimelinePoint:
    """Point on the forecast timeline for charting balances.

    Attributes:
        date: ISO date or datetime identifying the point on the timeline.
        label: Display label aligned to the frontend's chart axis.
        forecast_balance: Projected balance for the date.
        actual_balance: Actual balance when available.
        delta: Optional difference between forecast and actual balances.
        metadata: Optional metadata for debugging or UI annotations.
    """

    date: DateLike
    label: str
    forecast_balance: float
    actual_balance: Optional[float] = None
    delta: Optional[float] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary representation."""
        return {
            "date": _serialize_value(self.date),
            "label": self.label,
            "forecast_balance": _serialize_value(self.forecast_balance),
            "actual_balance": _serialize_value(self.actual_balance),
            "delta": _serialize_value(self.delta),
            "metadata": _serialize_value(self.metadata),
        }


@dataclass
class ForecastCashflowItem:
    """Cashflow item that contributes to the forecast projection.

    Attributes:
        date: ISO date or datetime for the cashflow event.
        amount: Signed amount (positive for inflow, negative for outflow).
        label: Human-readable label for the cashflow line item.
        category: Normalized category for grouping in breakdowns.
        source: Source system (e.g., recurring, manual, transaction).
        type: Cashflow type ("income" or "expense") for display.
        confidence: Confidence score for the source attribution.
        account_id: Optional account identifier.
        recurring_id: Optional recurring transaction identifier.
        direction: Optional direction hint ("inflow" or "outflow").
        sources: Optional source references that explain where this line item came from.
        metadata: Optional metadata for extended breakdowns.
    """

    date: DateLike
    amount: float
    label: str
    category: str
    source: str
    type: Optional[str] = None
    confidence: Optional[float] = None
    account_id: Optional[int] = None
    recurring_id: Optional[int] = None
    direction: Optional[str] = None
    sources: Optional[list[dict[str, Any]]] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary representation."""
        return {
            "date": _serialize_value(self.date),
            "amount": _serialize_value(self.amount),
            "label": self.label,
            "category": self.category,
            "source": self.source,
            "type": self.type,
            "confidence": _serialize_value(self.confidence),
            "account_id": self.account_id,
            "recurring_id": self.recurring_id,
            "direction": self.direction,
            "sources": _serialize_value(self.sources),
            "metadata": _serialize_value(self.metadata),
        }


@dataclass
class ForecastSeriesPoint:
    """Point within an aspect-specific daily chart series.

    Attributes:
        date: ISO date or datetime for the series point.
        label: Display label aligned to the shared chart axis.
        value: Numeric value for the aspect on the given day.
        metadata: Optional metadata for UI annotations.
    """

    date: DateLike
    label: str
    value: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary representation."""
        return {
            "date": _serialize_value(self.date),
            "label": self.label,
            "value": _serialize_value(self.value),
            "metadata": _serialize_value(self.metadata),
        }


@dataclass
class ForecastAspectSeries:
    """Named aspect-specific chart series attached to a forecast result.

    Attributes:
        id: Stable identifier for the series.
        label: Human-readable series label for UI copy.
        points: Daily points belonging to the series.
        metadata: Optional metadata for chart configuration or diagnostics.
    """

    id: ForecastSeriesId
    label: str
    points: list[ForecastSeriesPoint] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary representation."""
        return {
            "id": self.id,
            "label": self.label,
            "points": [point.to_dict() for point in self.points],
            "metadata": _serialize_value(self.metadata),
        }


ForecastSeriesMap: TypeAlias = dict[ForecastSeriesId, ForecastAspectSeries]


@dataclass
class ForecastSeriesCollection:
    """Top-level typed collection of aspect-specific chart series.

    The API serializes this collection as a `series` object keyed by stable aspect
    names so the frontend can read user-visible datasets directly instead of
    reverse-engineering them from generic cashflow rows.
    """

    realized_income: Optional[ForecastAspectSeries] = None
    manual_adjustments: Optional[ForecastAspectSeries] = None
    spending: Optional[ForecastAspectSeries] = None
    debt_totals: Optional[ForecastAspectSeries] = None

    def to_dict(self) -> dict[str, Any]:
        """Return the keyed aspect-series object used by the API payload."""
        series: ForecastSeriesMap = {}
        if self.realized_income is not None:
            series["realized_income"] = self.realized_income
        if self.manual_adjustments is not None:
            series["manual_adjustments"] = self.manual_adjustments
        if self.spending is not None:
            series["spending"] = self.spending
        if self.debt_totals is not None:
            series["debt_totals"] = self.debt_totals
        return {key: value.to_dict() for key, value in series.items()}


@dataclass
class ForecastAdjustment:
    """Manual or automated adjustment applied to the forecast model.

    Attributes:
        label: Display name for the adjustment.
        amount: Signed amount applied by the adjustment.
        date: ISO date or datetime when the adjustment applies.
        adjustment_type: Type of adjustment (e.g., manual, override).
        reason: Optional explanation of the adjustment.
        adjustment_id: Optional identifier for audit or updates.
        metadata: Optional metadata for extended UI context.
    """

    label: str
    amount: float
    date: DateLike
    adjustment_type: str
    reason: Optional[str] = None
    adjustment_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary representation."""
        return {
            "label": self.label,
            "amount": _serialize_value(self.amount),
            "date": _serialize_value(self.date),
            "adjustment_type": self.adjustment_type,
            "reason": self.reason,
            "adjustment_id": self.adjustment_id,
            "metadata": _serialize_value(self.metadata),
        }


@dataclass
class ForecastSummary:
    """Summary metrics for the forecast horizon.

    Attributes:
        start_date: ISO start date for the forecast window.
        end_date: ISO end date for the forecast window.
        starting_balance: Balance at the beginning of the horizon.
        ending_balance: Balance at the end of the horizon.
        net_change: Net change over the horizon.
        total_inflows: Total projected inflows.
        total_outflows: Total projected outflows.
        average_daily_change: Average daily delta across the horizon.
        min_balance: Minimum projected balance.
        max_balance: Maximum projected balance.
        depletion_date: First date where the balance is at or below zero.
        currency: ISO currency code for display.
        breakdowns: Category breakdowns used for summary widgets.
        account_count: Optional number of accounts contributing.
        recurring_count: Optional recurring transaction count.
        metadata: Optional metadata for UI or diagnostics.
    """

    start_date: DateLike
    end_date: DateLike
    starting_balance: float
    ending_balance: float
    net_change: float
    total_inflows: float
    total_outflows: float
    average_daily_change: float
    min_balance: float
    max_balance: float
    depletion_date: Optional[DateLike] = None
    currency: str = "USD"
    breakdowns: dict[str, float] = field(default_factory=dict)
    account_count: Optional[int] = None
    recurring_count: Optional[int] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary representation."""
        return {
            "start_date": _serialize_value(self.start_date),
            "end_date": _serialize_value(self.end_date),
            "starting_balance": _serialize_value(self.starting_balance),
            "ending_balance": _serialize_value(self.ending_balance),
            "net_change": _serialize_value(self.net_change),
            "total_inflows": _serialize_value(self.total_inflows),
            "total_outflows": _serialize_value(self.total_outflows),
            "average_daily_change": _serialize_value(self.average_daily_change),
            "min_balance": _serialize_value(self.min_balance),
            "max_balance": _serialize_value(self.max_balance),
            "depletion_date": _serialize_value(self.depletion_date),
            "currency": self.currency,
            "breakdowns": _serialize_value(self.breakdowns),
            "account_count": self.account_count,
            "recurring_count": self.recurring_count,
            "metadata": _serialize_value(self.metadata),
        }


@dataclass
class ForecastResult:
    """Forecast response payload delivered to the frontend.

    Attributes:
        timeline: Sequence of timeline points for charting balances.
        summary: Summary statistics for the forecast horizon.
        cashflows: List of cashflow line items that drive the forecast.
        adjustments: Manual or automated adjustments applied to the forecast.
        series: Typed aspect-series collection keyed by stable aspect name.
        metadata: Additional metadata for diagnostics or UI features.
    """

    timeline: list[ForecastTimelinePoint] = field(default_factory=list)
    summary: Optional[ForecastSummary] = None
    cashflows: list[ForecastCashflowItem] = field(default_factory=list)
    adjustments: list[ForecastAdjustment] = field(default_factory=list)
    series: ForecastSeriesCollection = field(default_factory=ForecastSeriesCollection)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return the full forecast response payload for JSON serialization."""
        return {
            "timeline": [point.to_dict() for point in self.timeline],
            "summary": self.summary.to_dict() if self.summary else None,
            "cashflows": [item.to_dict() for item in self.cashflows],
            "adjustments": [item.to_dict() for item in self.adjustments],
            "series": self.series.to_dict(),
            "metadata": _serialize_value(self.metadata),
        }


# ---------------------------------------------------------------------------
# Forecast V2 (event-driven liquid-cash ledger). Independent of the V1 response
# models above; V1 serialization is unchanged.
# ---------------------------------------------------------------------------


def _cents(value: Decimal) -> float:
    """Serialize a cent-quantized Decimal as a plain float."""
    return float(value)


@dataclass(frozen=True)
class ForecastV2Event:
    """One dated, signed cash/liability effect fed to the V2 ledger.

    Sign convention: for ``scheduled_income`` / ``scheduled_bill`` / ``adjustment`` /
    ``residual`` the ``amount`` is the signed effect on cash (deposit positive, debit
    negative). For ``transfer``, ``liability_payment`` and ``liability_charge`` the
    ``amount`` is a positive magnitude and direction comes from ``account_id`` (source)
    and ``counterparty_account_id`` (destination). Provider signs must be normalized
    once at the adapter boundary, never inferred here.

    Attributes:
        event_id: Stable instance identifier (``source:source_id:YYYY-MM-DD``).
        date: Calendar day the effect lands on.
        amount: Cent-quantized Decimal amount (see sign convention).
        account_id: Cash account affected, or the source account of a transfer.
        kind: One of ``EVENT_KINDS``.
        source_id: Identifier of the originating rule/transaction/adjustment.
        source: Origin family (``recurring``, ``manual``, ``residual`` ...).
        confidence: Optional 0-1 confidence in the event.
        counterparty_account_id: Destination account for transfers/payments.
        override: When True this event replaces another with the same ``event_id``.
        metadata: JSON-safe provenance.
    """

    event_id: str
    date: date
    amount: Decimal
    account_id: Optional[str]
    kind: str
    source_id: Optional[str] = None
    source: str = "manual"
    confidence: Optional[float] = None
    counterparty_account_id: Optional[str] = None
    override: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary (amount as a fixed 2-decimal string)."""
        return {
            "event_id": self.event_id,
            "date": self.date.isoformat(),
            "amount": f"{self.amount:.2f}",
            "account_id": self.account_id,
            "counterparty_account_id": self.counterparty_account_id,
            "kind": self.kind,
            "source_id": self.source_id,
            "source": self.source,
            "confidence": self.confidence,
            "override": self.override,
            "metadata": _serialize_value(self.metadata),
        }


@dataclass
class ForecastV2DailyPoint:
    """One calendar day of the V2 ledger.

    Cash and net worth are separate fields and never share a value.
    Invariants (cent-exact): ``ending_cash == starting_cash + inflows - outflows +
    adjustments`` and ``net_worth == ending_cash + other_assets + investment_value -
    liability_balance``.
    """

    date: date
    starting_cash: Decimal
    inflows: Decimal
    outflows: Decimal
    adjustments: Decimal
    ending_cash: Decimal
    event_ids: list[str]
    cash_by_account: dict[str, Decimal]
    liability_balance: Decimal
    investment_value: Decimal
    other_assets: Decimal
    net_worth: Decimal

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary representation."""
        return {
            "date": self.date.isoformat(),
            "starting_cash": _cents(self.starting_cash),
            "inflows": _cents(self.inflows),
            "outflows": _cents(self.outflows),
            "adjustments": _cents(self.adjustments),
            "ending_cash": _cents(self.ending_cash),
            "event_ids": list(self.event_ids),
            "cash_by_account": {key: _cents(self.cash_by_account[key]) for key in sorted(self.cash_by_account)},
            "liability_balance": _cents(self.liability_balance),
            "investment_value": _cents(self.investment_value),
            "other_assets": _cents(self.other_assets),
            "net_worth": _cents(self.net_worth),
        }


@dataclass
class ForecastV2Result:
    """Deterministic output of the V2 cash ledger.

    Attributes:
        status: ``ok`` or ``insufficient_data`` (no eligible liquid-cash account).
        start_date: First projected day (inclusive).
        end_date: Last projected day (inclusive).
        horizon_days: Number of projected calendar days.
        daily: One point per calendar day, including zero-event days.
        events: Events actually applied, ordered by ``(date, event_id)``.
        summary: Aggregate metrics (cents as floats, dates as ISO strings).
        accounts: Included/excluded account ids grouped by bucket.
        warnings: Data-quality warnings, each ``{"code", "message", ...}``.
        baseline: Always True; marks this as the no-scenario, no-uncertainty run.
    """

    status: str
    start_date: date
    end_date: date
    horizon_days: int
    daily: list[ForecastV2DailyPoint] = field(default_factory=list)
    events: list[ForecastV2Event] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    accounts: dict[str, Any] = field(default_factory=dict)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    baseline: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Return the JSON-serializable result; identical inputs give identical output."""
        return {
            "status": self.status,
            "baseline": self.baseline,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "horizon_days": self.horizon_days,
            "daily": [point.to_dict() for point in self.daily],
            "events": [event.to_dict() for event in self.events],
            "summary": _serialize_value(self.summary),
            "accounts": _serialize_value(self.accounts),
            "warnings": _serialize_value(self.warnings),
        }

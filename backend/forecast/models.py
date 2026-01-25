"""Typed models for forecast responses.

These dataclasses define the serialized shape of forecast responses delivered to the
frontend, including the timeline, summary, and supporting cashflow details.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Mapping, Optional, Sequence

DateLike = str | date | datetime


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
        account_id: Optional account identifier.
        recurring_id: Optional recurring transaction identifier.
        direction: Optional direction hint ("inflow" or "outflow").
        metadata: Optional metadata for extended breakdowns.
    """

    date: DateLike
    amount: float
    label: str
    category: str
    source: str
    account_id: Optional[int] = None
    recurring_id: Optional[int] = None
    direction: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary representation."""
        return {
            "date": _serialize_value(self.date),
            "amount": _serialize_value(self.amount),
            "label": self.label,
            "category": self.category,
            "source": self.source,
            "account_id": self.account_id,
            "recurring_id": self.recurring_id,
            "direction": self.direction,
            "metadata": _serialize_value(self.metadata),
        }


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
        metadata: Additional metadata for diagnostics or UI features.
    """

    timeline: list[ForecastTimelinePoint] = field(default_factory=list)
    summary: Optional[ForecastSummary] = None
    cashflows: list[ForecastCashflowItem] = field(default_factory=list)
    adjustments: list[ForecastAdjustment] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return the full forecast response payload for JSON serialization."""
        return {
            "timeline": [point.to_dict() for point in self.timeline],
            "summary": self.summary.to_dict() if self.summary else None,
            "cashflows": [item.to_dict() for item in self.cashflows],
            "adjustments": [item.to_dict() for item in self.adjustments],
            "metadata": _serialize_value(self.metadata),
        }

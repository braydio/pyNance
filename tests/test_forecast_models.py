import os
import sys
from datetime import date, datetime, timezone
from decimal import Decimal

BASE_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)

from forecast.models import (  # noqa: E402
    ForecastAdjustment,
    ForecastAspectSeries,
    ForecastCashflowItem,
    ForecastResult,
    ForecastSeriesCollection,
    ForecastSeriesPoint,
    ForecastSummary,
    ForecastTimelinePoint,
)


def test_forecast_result_to_dict_serializes_nested_models():
    timeline_point = ForecastTimelinePoint(
        date=date(2026, 1, 1),
        label="Jan 1",
        forecast_balance=Decimal("1200.50"),
        actual_balance=1100.0,
        delta=Decimal("100.50"),
        metadata={"note": "opening"},
    )
    cashflow_item = ForecastCashflowItem(
        date=datetime(2026, 1, 2, 8, 30, tzinfo=timezone.utc),
        amount=Decimal("250.00"),
        label="Paycheck",
        category="income",
        source="recurring",
        type="income",
        confidence=0.92,
        account_id=42,
        recurring_id=7,
        direction="inflow",
        sources=[
            {
                "type": "recurring_rule",
                "transaction_id": "txn-100",
                "category_display": "Income - Wages",
            }
        ],
        metadata={"tags": ["salary"]},
    )
    adjustment = ForecastAdjustment(
        label="Manual Override",
        amount=Decimal("-50.00"),
        date=date(2026, 1, 3),
        adjustment_type="manual",
        reason="One-off bill",
        adjustment_id="adj-001",
        metadata={"approved_by": "ops"},
    )
    manual_series = ForecastAspectSeries(
        id="manual_adjustments",
        label="Manual adjustments",
        points=[
            ForecastSeriesPoint(
                date=date(2026, 1, 2),
                label="2026-01-02",
                value=Decimal("-50.00"),
                metadata={"source": "manual"},
            )
        ],
        metadata={"timeframe": "forecast"},
    )
    summary = ForecastSummary(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        starting_balance=Decimal("1000.00"),
        ending_balance=Decimal("1500.00"),
        net_change=Decimal("500.00"),
        total_inflows=Decimal("800.00"),
        total_outflows=Decimal("300.00"),
        average_daily_change=Decimal("16.13"),
        min_balance=Decimal("900.00"),
        max_balance=Decimal("1600.00"),
        breakdowns={"income": Decimal("800.00"), "expenses": Decimal("300.00")},
        account_count=2,
        recurring_count=4,
        metadata={"sample": True},
    )
    result = ForecastResult(
        timeline=[timeline_point],
        summary=summary,
        cashflows=[cashflow_item],
        adjustments=[adjustment],
        series=ForecastSeriesCollection(manual_adjustments=manual_series),
        metadata={"generated_at": datetime(2026, 1, 1, tzinfo=timezone.utc)},
    )

    payload = result.to_dict()

    assert payload["timeline"][0]["date"] == "2026-01-01"
    assert payload["timeline"][0]["forecast_balance"] == 1200.5
    assert payload["cashflows"][0]["date"].startswith("2026-01-02T08:30:00")
    assert payload["adjustments"][0]["amount"] == -50.0
    assert payload["series"]["manual_adjustments"]["id"] == "manual_adjustments"
    assert payload["series"]["manual_adjustments"]["points"][0]["value"] == -50.0
    assert payload["cashflows"][0]["type"] == "income"
    assert payload["cashflows"][0]["confidence"] == 0.92
    assert payload["cashflows"][0]["sources"][0]["transaction_id"] == "txn-100"
    assert payload["summary"]["ending_balance"] == 1500.0
    assert payload["summary"]["breakdowns"] == {"income": 800.0, "expenses": 300.0}
    assert payload["metadata"]["generated_at"].startswith("2026-01-01T00:00:00")

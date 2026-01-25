import os
import sys
from datetime import date
from decimal import Decimal

BASE_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)

from forecast.engine import (  # noqa: E402
    apply_adjustments,
    build_cashflow_items,
    project_balances,
)
from forecast.models import ForecastTimelinePoint  # noqa: E402


def test_project_balances_uses_latest_snapshots_and_daily_averages():
    snapshots = [
        {"account_id": "acct-1", "balance": 100.0, "date": "2024-01-01", "user_id": 11},
        {"account_id": "acct-1", "balance": 150.0, "date": "2024-01-05", "user_id": 11},
        {"account_id": "acct-2", "balance": 200.0, "date": "2024-01-02", "user_id": 11},
        {"account_id": "acct-2", "balance": 180.0, "date": "2023-12-30", "user_id": 11},
        {"account_id": "acct-3", "balance": 999.0, "date": "2024-01-03", "user_id": 99},
    ]
    aggregates = [
        {"date": "2023-12-30", "inflow": 100.0, "outflow": 40.0},
        {"date": "2023-12-31", "inflow": 80.0, "outflow": 20.0},
    ]

    timeline = project_balances(
        user_id=11,
        start_date=date(2024, 1, 6),
        horizon_days=3,
        latest_snapshots=snapshots,
        historical_aggregates=aggregates,
    )

    balances = [point.forecast_balance for point in timeline]

    assert balances == [410.0, 470.0, 530.0]
    assert [point.label for point in timeline] == [
        "2024-01-06",
        "2024-01-07",
        "2024-01-08",
    ]


def test_project_balances_handles_empty_inputs():
    timeline = project_balances(
        user_id=1,
        start_date="2024-02-01",
        horizon_days=2,
        latest_snapshots=[],
        historical_aggregates=[],
    )

    assert [point.forecast_balance for point in timeline] == [0.0, 0.0]
    assert [point.label for point in timeline] == ["2024-02-01", "2024-02-02"]


def test_apply_adjustments_applies_recurring_and_preserves_baseline():
    baseline = [
        ForecastTimelinePoint(
            date=date(2024, 1, 1),
            label="2024-01-01",
            forecast_balance=100.0,
        ),
        ForecastTimelinePoint(
            date=date(2024, 1, 2),
            label="2024-01-02",
            forecast_balance=110.0,
        ),
        ForecastTimelinePoint(
            date=date(2024, 1, 3),
            label="2024-01-03",
            forecast_balance=120.0,
        ),
    ]
    adjustments = [
        {
            "label": "Daily Savings",
            "amount": 2.0,
            "date": "2024-01-01",
            "frequency": "daily",
        },
        {"label": "One-Time Fee", "amount": -5.0, "date": "2024-01-02"},
    ]

    adjusted = apply_adjustments(baseline, adjustments)

    assert [point.forecast_balance for point in baseline] == [100.0, 110.0, 120.0]
    assert [point.forecast_balance for point in adjusted] == [102.0, 109.0, 121.0]
    assert adjusted[1].metadata["baseline_balance"] == 110.0
    assert adjusted[1].metadata["adjustment_total"] == -1.0


def test_build_cashflow_items_matches_deltas_and_adjustments():
    timeline = [
        ForecastTimelinePoint(
            date=date(2024, 1, 1),
            label="2024-01-01",
            forecast_balance=110.0,
            metadata={"starting_balance": 100.0},
        ),
        ForecastTimelinePoint(
            date=date(2024, 1, 2),
            label="2024-01-02",
            forecast_balance=130.0,
        ),
    ]
    category_averages = [
        {"category": "Salary", "amount": 15.0},
        {"category": "Bills", "amount": -5.0},
    ]
    recurring_sources = [
        {"label": "Gym", "amount": -10.0, "date": "2024-01-02"},
    ]
    adjustments = [
        {"label": "Bonus", "amount": 5.0, "date": "2024-01-02"},
    ]

    items = build_cashflow_items(
        timeline,
        category_averages=category_averages,
        recurring_sources=recurring_sources,
        adjustments=adjustments,
    )

    totals: dict[date, Decimal] = {}
    for item in items:
        item_date = date.fromisoformat(str(item.date))
        totals[item_date] = totals.get(item_date, Decimal("0")) + Decimal(
            str(item.amount)
        )

    assert totals[date(2024, 1, 1)] == Decimal("10")
    assert totals[date(2024, 1, 2)] == Decimal("25")

    gym_item = next(item for item in items if item.label == "Gym")
    assert gym_item.source == "recurring"
    assert gym_item.type == "expense"
    assert gym_item.confidence == 0.85


def test_build_cashflow_items_uses_uncategorized_fallback():
    timeline = [
        ForecastTimelinePoint(
            date=date(2024, 2, 1),
            label="2024-02-01",
            forecast_balance=105.0,
            metadata={"starting_balance": 100.0},
        )
    ]

    items = build_cashflow_items(timeline)

    assert len(items) == 1
    assert items[0].label == "Uncategorized"
    assert items[0].source == "uncategorized"
    assert Decimal(str(items[0].amount)) == Decimal("5")

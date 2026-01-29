import os
import sys
from datetime import date

BASE_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)

from forecast.engine import (  # noqa: E402
    apply_adjustments,
    build_cashflow_items,
    compute_forecast,
    compute_summary,
)
from forecast.models import ForecastTimelinePoint  # noqa: E402


def test_compute_summary_reports_depletion_and_balances():
    """Validate summary fields for a depleted timeline."""
    timeline = [
        ForecastTimelinePoint(
            date=date(2026, 1, 1),
            label="2026-01-01",
            forecast_balance=80.0,
            metadata={"starting_balance": 100.0},
        ),
        ForecastTimelinePoint(
            date=date(2026, 1, 2),
            label="2026-01-02",
            forecast_balance=-10.0,
        ),
    ]

    summary = compute_summary(timeline)

    assert summary.starting_balance == 100.0
    assert summary.ending_balance == -10.0
    assert summary.net_change == -110.0
    assert summary.min_balance == -10.0
    assert summary.depletion_date == date(2026, 1, 2)


def test_compute_forecast_serializes_full_payload():
    """Ensure compute_forecast returns fully serialized payloads."""
    payload = compute_forecast(
        user_id=1,
        start_date=date(2026, 1, 1),
        horizon_days=2,
        latest_snapshots=[{"account_id": "a1", "balance": 100.0, "date": "2026-01-01"}],
        historical_aggregates=[{"date": "2025-12-31", "inflow": 20.0, "outflow": 10.0}],
        adjustments=[
            {
                "label": "One-off",
                "amount": -50.0,
                "date": "2026-01-01",
                "adjustment_type": "manual",
            }
        ],
    )

    assert payload["timeline"][0]["forecast_balance"] == 60.0
    assert payload["timeline"][1]["forecast_balance"] == 70.0
    assert payload["summary"]["starting_balance"] == 100.0
    assert payload["summary"]["ending_balance"] == 70.0
    assert payload["summary"]["depletion_date"] is None
    assert payload["adjustments"][0]["amount"] == -50.0


def test_compute_forecast_is_deterministic():
    """Confirm identical inputs produce identical forecast payloads."""
    inputs = dict(
        user_id=7,
        start_date=date(2026, 3, 1),
        horizon_days=3,
        latest_snapshots=[{"account_id": "a1", "balance": 200.0, "date": "2026-03-01"}],
        historical_aggregates=[{"date": "2026-02-28", "inflow": 30.0, "outflow": 10.0}],
        adjustments=[
            {
                "label": "Manual tweak",
                "amount": -25.0,
                "date": "2026-03-02",
                "adjustment_type": "manual",
            }
        ],
    )

    first_payload = compute_forecast(**inputs)
    second_payload = compute_forecast(**inputs)

    assert first_payload == second_payload


def test_apply_adjustments_handles_overlap_and_removal():
    """Ensure overlapping adjustments aggregate and later removals unwind them."""
    baseline = [
        ForecastTimelinePoint(
            date=date(2026, 1, 1),
            label="2026-01-01",
            forecast_balance=100.0,
        ),
        ForecastTimelinePoint(
            date=date(2026, 1, 2),
            label="2026-01-02",
            forecast_balance=110.0,
        ),
        ForecastTimelinePoint(
            date=date(2026, 1, 3),
            label="2026-01-03",
            forecast_balance=120.0,
        ),
    ]
    adjustments = [
        {"label": "Bonus", "amount": 10.0, "date": "2026-01-01"},
        {"label": "Extra", "amount": 5.0, "date": "2026-01-01"},
        {"label": "Remove", "amount": -15.0, "date": "2026-01-02"},
    ]

    adjusted = apply_adjustments(baseline, adjustments)

    assert adjusted[0].forecast_balance == 115.0
    assert adjusted[1].forecast_balance == 110.0
    assert adjusted[2].forecast_balance == 120.0
    assert adjusted[0].metadata["adjustment_total"] == 15.0
    assert adjusted[1].metadata["adjustment_total"] == 0.0


def test_compute_summary_reports_min_balance_and_depletion_date():
    """Verify summary min balance and depletion date detection."""
    timeline = [
        ForecastTimelinePoint(
            date=date(2026, 2, 1),
            label="2026-02-01",
            forecast_balance=40.0,
            metadata={"starting_balance": 60.0},
        ),
        ForecastTimelinePoint(
            date=date(2026, 2, 2),
            label="2026-02-02",
            forecast_balance=10.0,
        ),
        ForecastTimelinePoint(
            date=date(2026, 2, 3),
            label="2026-02-03",
            forecast_balance=-5.0,
        ),
    ]

    summary = compute_summary(timeline)

    assert summary.min_balance == -5.0
    assert summary.depletion_date == date(2026, 2, 3)


def test_cashflow_items_sum_to_timeline_deltas():
    """Assert cashflow totals per day equal timeline deltas."""
    timeline = [
        ForecastTimelinePoint(
            date=date(2026, 4, 1),
            label="2026-04-01",
            forecast_balance=110.0,
            metadata={"starting_balance": 100.0},
        ),
        ForecastTimelinePoint(
            date=date(2026, 4, 2),
            label="2026-04-02",
            forecast_balance=105.0,
        ),
        ForecastTimelinePoint(
            date=date(2026, 4, 3),
            label="2026-04-03",
            forecast_balance=120.0,
        ),
    ]

    cashflows = build_cashflow_items(timeline)
    cashflow_totals: dict[date, float] = {}
    for item in cashflows:
        cashflow_totals[item.date] = cashflow_totals.get(item.date, 0.0) + item.amount

    previous_balance = 100.0
    for point in timeline:
        delta = point.forecast_balance - previous_balance
        assert cashflow_totals[point.date] == delta
        previous_balance = point.forecast_balance

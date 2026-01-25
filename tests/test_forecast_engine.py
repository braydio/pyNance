import os
import sys
from datetime import date

BASE_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)

from forecast.engine import compute_forecast, compute_summary  # noqa: E402
from forecast.models import ForecastTimelinePoint  # noqa: E402


def test_compute_summary_reports_depletion_and_balances():
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

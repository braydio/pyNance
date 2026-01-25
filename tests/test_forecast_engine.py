from datetime import date
import os
import sys

BASE_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)

from forecast.engine import project_balances  # noqa: E402


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

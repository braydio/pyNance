import os
import importlib.util
from datetime import date

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")

spec = importlib.util.spec_from_file_location(
    "account_history", os.path.join(BASE_BACKEND, "app", "services", "account_history.py")
)
account_history = importlib.util.module_from_spec(spec)
spec.loader.exec_module(account_history)
compute_balance_history = account_history.compute_balance_history


def test_compute_balance_history_reverse_mapping():
    txs = [
        {"date": date(2025, 8, 2), "amount": 25.0},
        {"date": date(2025, 8, 1), "amount": -50.0},
    ]
    start = date(2025, 8, 1)
    end = date(2025, 8, 3)
    result = compute_balance_history(100.0, txs, start, end)
    assert result == [
        {"date": "2025-08-01", "balance": 75.0},
        {"date": "2025-08-02", "balance": 100.0},
        {"date": "2025-08-03", "balance": 100.0},
    ]


def test_compute_balance_history_fills_gaps():
    txs = []
    start = date(2025, 1, 1)
    end = date(2025, 1, 3)
    result = compute_balance_history(10.0, txs, start, end)
    assert len(result) == 3
    assert result[0]["date"] == "2025-01-01"
    assert result[-1]["balance"] == 10.0

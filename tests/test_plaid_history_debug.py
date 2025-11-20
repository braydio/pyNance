"""Tests for the Plaid history debug utilities."""

from datetime import date
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).parent.parent / "backend/app/cli/debug_plaid_history.py"
SPEC = spec_from_file_location("debug_plaid_history", MODULE_PATH)
assert SPEC and SPEC.loader
debug_module = module_from_spec(SPEC)
SPEC.loader.exec_module(debug_module)
collect_full_history = debug_module.collect_full_history


@pytest.mark.parametrize("window_days", [5, 10])
def test_collect_full_history_deduplicates_and_tracks_missing(window_days):
    responses = {
        ("2024-01-06", "2024-01-10"): [
            {"transaction_id": "tx_1", "date": "2024-01-06"},
            {"transaction_id": "tx_2", "date": "2024-01-07"},
        ],
        ("2024-01-01", "2024-01-05"): [
            {"transaction_id": "tx_2", "date": "2024-01-07"},
            {"transaction_id": "tx_3", "date": "2024-01-02"},
            {"date": "2024-01-01", "name": "missing id"},
        ],
    }

    def fake_fetch(
        access_token: str, start: str, end: str
    ):  # pragma: no cover - simple shim
        if (start, end) in responses:
            return responses[(start, end)]
        return sum(responses.values(), [])

    report = collect_full_history(
        access_token="token",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 10),
        window_days=window_days,
        fetcher=fake_fetch,
    )

    assert report["total_seen"] == 5
    assert report["total_unique"] == 4  # tx_2 deduped once; missing-id txn included
    assert report["duplicate_transaction_ids"] == 1
    assert report["missing_transaction_ids"] == 1
    assert report["earliest_date"] == "2024-01-01"
    assert report["latest_date"] == "2024-01-07"
    expected_windows = 2 if window_days == 5 else 1
    assert len(report["windows"]) == expected_windows


def test_collect_full_history_rejects_invalid_ranges():
    with pytest.raises(ValueError):
        collect_full_history(
            access_token="token",
            start_date=date(2024, 2, 1),
            end_date=date(2024, 1, 1),
        )

    with pytest.raises(ValueError):
        collect_full_history(
            access_token="token",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1),
            window_days=0,
        )

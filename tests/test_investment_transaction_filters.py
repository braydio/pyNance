"""Unit tests for investment transaction filter parsing."""

import pytest

pytest.importorskip("flask", reason="flask is required to import investment routes")

from backend.app.routes.investments import parse_transaction_filter_params


def test_parse_transaction_filters_valid_payload():
    """Ensure the helper returns normalized filter values for valid input."""

    args = {
        "account_id": "acct-1",
        "security_id": "sec-1",
        "type": "buy",
        "subtype": "mutual fund",
        "start_date": "2024-01-15",
        "end_date": "2024-02-01",
    }

    filters = parse_transaction_filter_params(args)

    assert filters["account_id"] == "acct-1"
    assert filters["security_id"] == "sec-1"
    assert filters["type"] == "buy"
    assert filters["subtype"] == "mutual fund"
    assert str(filters["start_date"]) == "2024-01-15"
    assert str(filters["end_date"]) == "2024-02-01"


@pytest.mark.parametrize(
    "payload,expected_message",
    [
        ({"start_date": "20240115"}, "Invalid date"),
        (
            {"start_date": "2024-03-01", "end_date": "2024-02-01"},
            "end_date must be greater",
        ),
    ],
)
def test_parse_transaction_filters_invalid(payload, expected_message):
    """Invalid payloads should raise a ``ValueError`` with context."""

    with pytest.raises(ValueError) as excinfo:
        parse_transaction_filter_params(payload)

    assert expected_message in str(excinfo.value)

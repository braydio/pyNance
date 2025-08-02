"""Tests for Plaid ApiException handling in account refresh logic."""

import json
import types

from plaid import ApiException

from test_save_plaid_account import db_ctx  # noqa: F401


class DummyResponse:
    def __init__(self, data: str) -> None:
        self.data = data
        self.status = 400
        self.reason = "Bad"

    def getheaders(self) -> dict[str, str]:
        return {}


def test_refresh_data_for_plaid_account_returns_error_details(db_ctx, monkeypatch):  # noqa: F811
    db, models, logic = db_ctx
    acc = models.Account(
        account_id="acct1",
        user_id="u1",
        name="Checking",
        type="checking",
        institution_name="Bank",
    )
    db.session.add(acc)
    db.session.commit()

    monkeypatch.setattr(logic, "get_accounts", lambda *a, **k: [])

    def raise_api_exception(*a, **k):
        body = json.dumps({"error_code": "SOME_CODE", "error_message": "SOME_MESSAGE"})
        raise ApiException(http_resp=DummyResponse(body))

    monkeypatch.setattr(logic, "get_transactions", raise_api_exception)

    log_msgs: list[str] = []
    monkeypatch.setattr(
        logic,
        "logger",
        types.SimpleNamespace(
            info=lambda *a, **k: None,
            debug=lambda *a, **k: None,
            warning=lambda *a, **k: None,
            error=lambda msg, *a, **k: log_msgs.append(msg),
        ),
    )

    updated, err = logic.refresh_data_for_plaid_account("tok", "acct1")
    assert updated is False
    assert err == {
        "plaid_error_code": "SOME_CODE",
        "plaid_error_message": "SOME_MESSAGE",
    }
    assert any(
        "Bank / Checking" in m and "SOME_CODE" in m and "SOME_MESSAGE" in m
        for m in log_msgs
    )

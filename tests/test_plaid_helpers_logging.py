import logging
import os
from pathlib import Path

import pytest

os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")

from app.helpers import plaid_helpers


class _FakePlaidExchangeResponse:
    access_token = "access-token"
    item_id = "item-123"


class _FakePlaidClient:
    def __init__(self):
        self.last_request = None

    def item_public_token_exchange(self, request):
        self.last_request = request
        return _FakePlaidExchangeResponse()


def test_token_file_logging_redacts_values(tmp_path: Path, monkeypatch, caplog):
    token_path = tmp_path / "tokens.json"
    monkeypatch.setattr(plaid_helpers, "PLAID_TOKENS", token_path)

    with caplog.at_level(logging.INFO, logger=plaid_helpers.logger.name):
        plaid_helpers.save_plaid_tokens(["tok-123", "tok-456"])

    assert "tok-123" not in caplog.text
    assert "Saving 2 Plaid token(s)" in caplog.text
    assert str(token_path) in caplog.text

    caplog.clear()
    with caplog.at_level(logging.INFO, logger=plaid_helpers.logger.name):
        tokens = plaid_helpers.load_plaid_tokens()

    assert tokens == ["tok-123", "tok-456"]
    assert "tok-123" not in caplog.text
    assert "Loaded 2 Plaid token(s)" in caplog.text
    assert str(token_path) in caplog.text


def test_exchange_public_token_logs_without_public_value(monkeypatch, caplog):
    fake_client = _FakePlaidClient()
    monkeypatch.setattr(plaid_helpers, "plaid_client", fake_client)

    with caplog.at_level(logging.INFO, logger=plaid_helpers.logger.name):
        result = plaid_helpers.exchange_public_token("public-sample-token")

    assert result["item_id"] == _FakePlaidExchangeResponse.item_id
    assert "public-sample-token" not in caplog.text
    assert "Exchanging public token for access token" in caplog.text
    assert "Successfully exchanged token. Item ID: item-123" in caplog.text


def test_get_accounts_logs_error_for_missing_user(caplog):
    with caplog.at_level(logging.ERROR, logger=plaid_helpers.logger.name):
        with pytest.raises(ValueError):
            plaid_helpers.get_accounts("access-token", user_id="")

    assert "Missing user_id in get_accounts()" in caplog.text

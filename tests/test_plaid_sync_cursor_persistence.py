"""Regression checks for checkpoint consistency and calendar dates."""

from datetime import date, datetime, timezone

import pytest
from app.extensions import db
from app.models import Account, PlaidAccount
from app.services import plaid_sync
from test_plaid_ingestion_integrity import database as database_fixture

database = database_fixture


def test_parse_transaction_date_preserves_calendar_semantics():
    assert plaid_sync._parse_txn_date("2026-02-24") == date(2026, 2, 24)
    assert plaid_sync._parse_txn_date(datetime(2026, 2, 24, 0, 0, tzinfo=timezone.utc)) == date(2026, 2, 24)


def test_sync_rejects_divergent_item_cursors(database):
    db.session.add_all(
        [
            Account(account_id="sibling", user_id="owner", name="Savings"),
            PlaidAccount(account_id="sibling", item_id="item", access_token="x", sync_cursor="cursor-other"),
        ]
    )
    database[1].sync_cursor = "cursor-old"
    db.session.commit()
    with pytest.raises(ValueError, match="inconsistent sync checkpoints"):
        plaid_sync.sync_account_transactions("checking")

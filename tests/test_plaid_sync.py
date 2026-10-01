"""Item cursor persistence uses a single commit for every page and sibling account."""

from unittest.mock import patch

from app.extensions import db
from app.models import Account, PlaidAccount, Transaction
from app.services import plaid_sync
from test_plaid_ingestion_integrity import configure_sync, payload
from test_plaid_ingestion_integrity import database as database_fixture

database = database_fixture


def test_sync_persists_item_cursor_once_after_pages(database, monkeypatch):
    db.session.add_all(
        [
            Account(account_id="sibling", user_id="owner", name="Savings"),
            PlaidAccount(account_id="sibling", item_id="item", access_token="x", sync_cursor=None),
        ]
    )
    database[1].sync_cursor = "cursor-old"
    db.session.commit()
    configure_sync(
        monkeypatch,
        [
            {"added": [payload("first")], "next_cursor": "page-1", "has_more": True},
            {"added": [payload("second", account_id="sibling")], "next_cursor": "cursor-final", "has_more": False},
        ],
    )
    with patch.object(db.session, "commit", wraps=db.session.commit) as commit:
        result = plaid_sync.sync_account_transactions("checking")
    assert result["next_cursor"] == "cursor-final"
    assert commit.call_count == 1
    assert Transaction.query.count() == 2
    assert all(pa.sync_cursor == "cursor-final" for pa in PlaidAccount.query.all())

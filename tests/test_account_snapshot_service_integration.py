"""Integration tests for account snapshot service using a real database session."""

from __future__ import annotations

import os
import sys
from datetime import datetime

import pytest
from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)

for module in [
    "app",
    "app.config",
    "app.extensions",
    "app.models",
    "app.services",
    "app.services.account_snapshot",
]:
    sys.modules.pop(module, None)

from app.extensions import db
from app.models import Account, AccountSnapshotPreference
from app.services.account_snapshot import build_snapshot_payload


@pytest.fixture()
def sqlite_app():
    """Provide an isolated Flask app bound to an in-memory SQLite database."""
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite://",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    db.init_app(app)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def _make_account(
    account_id: str, name: str, balance: float, institution: str
) -> Account:
    """Create an :class:`Account` instance for integration testing."""
    return Account(
        account_id=account_id,
        user_id="integration-user",
        name=name,
        type="depository",
        subtype="checking",
        institution_name=institution,
        balance=balance,
        link_type="manual",
        is_hidden=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


def test_build_snapshot_payload_creates_preference_sqlite(sqlite_app):
    """`build_snapshot_payload` should persist defaults using an actual session."""
    with sqlite_app.app_context():
        accounts = [
            _make_account("acc-1", "Checking", 125.50, "First Bank"),
            _make_account("acc-2", "Savings", 980.00, "First Bank"),
            _make_account("acc-3", "Brokerage", 1540.75, "InvestCo"),
        ]
        db.session.add_all(accounts)
        db.session.commit()

        payload = build_snapshot_payload(user_id="integration-user")

        preference = AccountSnapshotPreference.query.filter_by(
            user_id="integration-user"
        ).first()
        assert preference is not None
        assert preference.selected_account_ids == ["acc-1", "acc-2", "acc-3"]

        assert payload["selected_account_ids"] == ["acc-1", "acc-2", "acc-3"]
        assert len(payload["selected_accounts"]) == 3
        assert {acc["account_id"] for acc in payload["available_accounts"]} == {
            "acc-1",
            "acc-2",
            "acc-3",
        }

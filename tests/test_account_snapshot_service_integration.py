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
from app.services.account_snapshot import (
    MAX_SNAPSHOT_SELECTION,
    build_snapshot_payload,
)


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
    account_id: str,
    name: str,
    balance: float,
    institution: str,
    account_type: str = "depository",
    subtype: str = "checking",
) -> Account:
    """Create an :class:`Account` instance for integration testing."""
    return Account(
        account_id=account_id,
        user_id="integration-user",
        name=name,
        type=account_type,
        subtype=subtype,
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
        asset_accounts = [
            _make_account("asset-1", "High-Yield Savings", 12500.0, "First Bank"),
            _make_account("asset-2", "Brokerage", 9600.0, "InvestCo"),
            _make_account("asset-3", "Retirement", 8300.0, "RetireWell"),
            _make_account("asset-4", "Emergency Fund", 6100.0, "Credit Union"),
            _make_account("asset-5", "Vacation Savings", 5400.0, "First Bank"),
            _make_account("asset-6", "Overflow Checking", 1800.0, "Credit Union"),
        ]
        liability_accounts = [
            _make_account(
                "liability-1",
                "Travel Rewards Card",
                8200.0,
                "Big Card",
                account_type="credit card",
                subtype="credit",
            ),
            _make_account(
                "liability-2",
                "Everyday Card",
                6100.0,
                "Everyday Bank",
                account_type="credit card",
                subtype="credit",
            ),
            _make_account(
                "liability-3",
                "Auto Loan",
                4700.0,
                "Auto Lender",
                account_type="loan",
                subtype="auto",
            ),
            _make_account(
                "liability-4",
                "Student Loan",
                3600.0,
                "Education Lender",
                account_type="loan",
                subtype="student",
            ),
            _make_account(
                "liability-5",
                "Store Card",
                2400.0,
                "Retail Bank",
                account_type="credit card",
                subtype="credit",
            ),
            _make_account(
                "liability-6",
                "Home Equity Line",
                1500.0,
                "Neighborhood Bank",
                account_type="loan",
                subtype="home",
            ),
        ]
        db.session.add_all(asset_accounts + liability_accounts)
        db.session.commit()

        payload = build_snapshot_payload(user_id="integration-user")

        preference = AccountSnapshotPreference.query.filter_by(
            user_id="integration-user"
        ).first()
        assert preference is not None
        expected_selection = [
            "asset-1",
            "asset-2",
            "asset-3",
            "asset-4",
            "asset-5",
            "liability-1",
            "liability-2",
            "liability-3",
            "liability-4",
            "liability-5",
        ]

        assert preference.selected_account_ids == expected_selection

        assert payload["selected_account_ids"] == expected_selection
        assert len(payload["selected_accounts"]) == len(expected_selection)
        assert payload["metadata"].get("max_selection") == MAX_SNAPSHOT_SELECTION
        assert {acc["account_id"] for acc in payload["available_accounts"]} == {
            acct.account_id for acct in asset_accounts + liability_accounts
        }

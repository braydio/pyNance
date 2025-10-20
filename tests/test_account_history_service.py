import os
import sys
from datetime import date
from decimal import Decimal

import pytest
from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")

if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)

os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
os.environ.setdefault("PLAID_CLIENT_ID", "sandbox-client")
os.environ.setdefault("PLAID_SECRET_KEY", "sandbox-secret")
os.environ.setdefault("CLIENT_NAME", "pyNance Test Suite")
os.environ.setdefault("BACKEND_PUBLIC_URL", "http://localhost")

from app.extensions import db
from app.models import Account
from app.services.account_history import compute_balance_history
from app.sql.account_logic import upsert_accounts


@pytest.fixture()
def app_context():
    """Provide an application context backed by an in-memory SQLite database."""

    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()


def test_compute_balance_history_reverse_mapping():
    txs = [
        {"date": date(2025, 8, 2), "amount": 25.0},
        {"date": date(2025, 8, 1), "amount": -50.0},
    ]
    start = date(2025, 8, 1)
    end = date(2025, 8, 3)
    result = compute_balance_history(Decimal("100.0"), txs, start, end)
    assert result == [
        {"date": "2025-08-01", "balance": 75.0},
        {"date": "2025-08-02", "balance": 100.0},
        {"date": "2025-08-03", "balance": 100.0},
    ]


def test_compute_balance_history_fills_gaps():
    txs = []
    start = date(2025, 1, 1)
    end = date(2025, 1, 3)
    result = compute_balance_history(Decimal("10.0"), txs, start, end)
    assert len(result) == 3
    assert result[0]["date"] == "2025-01-01"
    assert result[-1]["balance"] == 10.0


def test_upsert_accounts_normalizes_status(app_context):
    accounts = [
        {
            "account_id": "acct-1",
            "name": "Checking",
            "type": "depository",
            "balances": {"current": 100},
            "status": "ACTIVE",
        },
        {
            "account_id": "acct-2",
            "name": "Brokerage",
            "type": "investment",
            "balances": {"current": 50},
        },
        {
            "account_id": "acct-3",
            "name": "Credit",
            "type": "credit",
            "balances": {"current": -25},
            "status": "paused",
        },
    ]

    upsert_accounts("user-1", accounts, provider="PLAID")

    persisted = {
        account.account_id: account.status
        for account in Account.query.order_by(Account.account_id)
    }

    assert persisted == {
        "acct-1": "active",
        "acct-2": "active",
        "acct-3": "active",
    }

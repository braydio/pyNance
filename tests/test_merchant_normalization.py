"""Tests for merchant normalization and ingestion wiring."""

import os
import sys
from datetime import datetime, timezone
from decimal import Decimal

import pytest

import importlib.util
from pathlib import Path

from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)

os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
os.environ.setdefault("PLAID_CLIENT_ID", "sandbox-client")
os.environ.setdefault("PLAID_SECRET_KEY", "sandbox-secret")
os.environ.setdefault("CLIENT_NAME", "pyNance Test Suite")
os.environ.setdefault("BACKEND_PUBLIC_URL", "http://localhost")


if "app" in sys.modules and not hasattr(sys.modules["app"], "__path__"):
    del sys.modules["app"]

from app.extensions import db
from app.models import Account, PlaidAccount, Transaction
from app.utils.merchant_normalization import resolve_merchant


def _load_backend_module(relative_path: str, module_name: str):
    module_path = Path(BASE_BACKEND) / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def app_context():
    """Create an isolated in-memory app context for merchant normalization tests."""

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


@pytest.mark.parametrize(
    ("merchant_name", "name", "description", "expected_display", "expected_slug"),
    [
        ("", "POS STARBUCKS 12345", None, "Starbucks 12345", "starbucks-12345"),
        (None, "SQ *JOES COFFEE", None, "Joes Coffee", "joes-coffee"),
        (None, None, "PAYPAL *NETFLIX.COM", "Netflix.com", "netflix-com"),
        ("  Whole Foods  ", "POS SHOULD NOT WIN", None, "Whole Foods", "whole-foods"),
    ],
)
def test_resolve_merchant_normalizes_noisy_values(
    merchant_name, name, description, expected_display, expected_slug
):
    """Normalization should strip processor noise and return stable slugs."""

    resolved = resolve_merchant(
        merchant_name=merchant_name, name=name, description=description
    )

    assert resolved.display_name == expected_display
    assert resolved.merchant_slug == expected_slug


def test_upsert_transaction_uses_normalized_merchant_name(app_context):
    """Plaid sync upserts should write normalized merchant names and preserve descriptions."""

    account = Account(
        account_id="acc-1",
        user_id="user-1",
        name="Checking",
        type="depository",
        balance=Decimal("100.00"),
    )
    plaid_account = PlaidAccount(
        account_id="acc-1",
        item_id="item-1",
        access_token="token",
    )
    db.session.add_all([account, plaid_account])
    db.session.commit()

    tx = {
        "transaction_id": "tx-sync-1",
        "account_id": "acc-1",
        "amount": 9.99,
        "date": "2024-04-01",
        "name": "POS SQ *JOES COFFEE",
        "description": "POS SQ *JOES COFFEE",
        "merchant_name": "",
        "category": ["Food and Drink", "Coffee Shop"],
        "payment_meta": {"payment_method": "card"},
    }

    plaid_sync = _load_backend_module(
        "app/services/plaid_sync.py", "merchant_test_plaid_sync"
    )
    plaid_sync._upsert_transaction(tx, account, plaid_account)
    db.session.commit()

    saved = Transaction.query.filter_by(transaction_id="tx-sync-1").first()
    assert saved is not None
    assert saved.description == "POS SQ *JOES COFFEE"
    assert saved.merchant_name == "Joes Coffee"
    assert saved.plaid_meta.raw["merchant_slug"] == "joes-coffee"


def test_refresh_data_for_plaid_account_uses_normalized_merchant_name(
    app_context, monkeypatch
):
    """Legacy refresh path should apply the same merchant normalization helper."""

    account = Account(
        account_id="acc-refresh-1",
        user_id="user-1",
        name="Checking",
        type="depository",
        balance=Decimal("100.00"),
    )
    plaid_account = PlaidAccount(
        account_id="acc-refresh-1",
        item_id="item-refresh-1",
        access_token="token",
        last_refreshed=datetime.now(timezone.utc),
    )
    db.session.add_all([account, plaid_account])
    db.session.commit()

    sample_transactions = [
        {
            "transaction_id": "tx-refresh-1",
            "account_id": "acc-refresh-1",
            "amount": 19.50,
            "date": "2024-05-01",
            "name": "POS PAYPAL *NETFLIX.COM",
            "description": "POS PAYPAL *NETFLIX.COM",
            "merchant_name": "",
            "category": ["Service", "Streaming"],
            "pending": False,
            "payment_meta": {"payment_method": "online"},
            "personal_finance_category": {
                "primary": "ENTERTAINMENT",
                "detailed": "ENTERTAINMENT_TV_AND_MOVIES",
            },
        }
    ]

    account_logic = _load_backend_module(
        "app/sql/account_logic.py", "merchant_test_account_logic"
    )

    monkeypatch.setattr(
        account_logic,
        "get_transactions",
        lambda *args, **kwargs: sample_transactions,
    )

    updated, error = account_logic.refresh_data_for_plaid_account(
        access_token="token",
        account_or_id=account,
        accounts_data=[{"account_id": "acc-refresh-1", "balances": {"current": 100.0}}],
    )

    assert updated is True
    assert error is None

    saved = Transaction.query.filter_by(transaction_id="tx-refresh-1").first()
    assert saved is not None
    assert saved.description == "POS PAYPAL *NETFLIX.COM"
    assert saved.merchant_name == "Netflix.com"
    assert saved.plaid_meta.raw["merchant_slug"] == "netflix-com"

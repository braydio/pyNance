"""Tests that internal transfers are excluded from spend analytics endpoints."""

import os
import sys
from datetime import datetime, timezone
from decimal import Decimal

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
from app.models import Account, Category, Transaction
from app.routes.summary import summary
from app.routes.transactions import transactions
from app.sql.account_logic import get_paginated_transactions


def _seed_analytics_fixture() -> None:
    food = Category(
        primary_category="Food and Drink",
        detailed_category="Restaurants",
        category_slug="FOOD_AND_DRINK_RESTAURANTS",
        category_display="Food and Drink - Restaurants",
    )
    db.session.add(food)

    checking = Account(
        account_id="analytics-checking",
        user_id="analytics-user",
        name="Checking",
        type="depository",
    )
    savings = Account(
        account_id="analytics-savings",
        user_id="analytics-user",
        name="Savings",
        type="depository",
        subtype="savings",
    )
    db.session.add_all([checking, savings])
    db.session.flush()

    rows = [
        Transaction(
            transaction_id="spend-1",
            account_id="analytics-checking",
            user_id="analytics-user",
            amount=Decimal("25.00"),
            date=datetime(2024, 4, 20, tzinfo=timezone.utc),
            description="Lunch",
            category_id=food.id,
            category=food.category_display,
            category_slug=food.category_slug,
            category_display=food.category_display,
            merchant_name="Cafe",
            is_internal=False,
        ),
        Transaction(
            transaction_id="transfer-1",
            account_id="analytics-checking",
            user_id="analytics-user",
            amount=Decimal("-200.00"),
            date=datetime(2024, 4, 20, tzinfo=timezone.utc),
            description="Transfer to savings",
            merchant_name="Internal Transfer",
            is_internal=True,
            transfer_type="checking_savings_transfer",
        ),
        Transaction(
            transaction_id="transfer-2",
            account_id="analytics-savings",
            user_id="analytics-user",
            amount=Decimal("200.00"),
            date=datetime(2024, 4, 20, tzinfo=timezone.utc),
            description="Transfer from checking",
            merchant_name="Internal Transfer",
            is_internal=True,
            transfer_type="checking_savings_transfer",
        ),
    ]
    db.session.add_all(rows)
    db.session.commit()


def _build_client():
    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite://",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    db.init_app(app)
    app.register_blueprint(summary, url_prefix="/summary")
    app.register_blueprint(transactions, url_prefix="/transactions")

    with app.app_context():
        db.create_all()
        _seed_analytics_fixture()

    return app.test_client(), app


def test_transaction_reporting_excludes_internal_transfers():
    _client, app = _build_client()
    with app.app_context():
        rows, total, _meta = get_paginated_transactions(
            page=1,
            page_size=50,
            start_date=datetime(2024, 4, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 4, 30, tzinfo=timezone.utc),
            user_id="analytics-user",
        )

    assert total == 1
    assert len(rows) == 1
    assert rows[0]["transaction_id"] == "spend-1"
    assert rows[0]["internal_transfer_flag"] is False


def test_top_spending_category_excludes_internal_transfers():
    client, app = _build_client()
    with app.app_context():
        response = client.get(
            "/transactions/top_categories?start_date=2024-04-01&end_date=2024-04-30"
        )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == "Food and Drink - Restaurants"
    assert data[0]["total"] == 25.0

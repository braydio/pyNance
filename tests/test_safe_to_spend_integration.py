"""Database-backed coverage for the Safe-to-Spend dashboard route."""

import os
from datetime import date
from decimal import Decimal

os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
os.environ.setdefault("PLAID_CLIENT_ID", "sandbox-client")
os.environ.setdefault("PLAID_SECRET_KEY", "sandbox-secret")
os.environ.setdefault("CLIENT_NAME", "pyNance Test Suite")
os.environ.setdefault("BACKEND_PUBLIC_URL", "http://localhost")

import pytest
from app.extensions import db
from app.models import Account, PlannedBill, PlanningScenario, Transaction
from app.routes.dashboard import dashboard
from flask import Flask


@pytest.fixture()
def safe_to_spend_client():
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        TESTING=True,
    )
    db.init_app(app)
    app.register_blueprint(dashboard, url_prefix="/api/dashboard")
    with app.app_context():
        db.create_all()
        with app.test_client() as client:
            yield client
        db.session.remove()
        db.drop_all()


def test_safe_to_spend_route_queries_accounts_transactions_and_planned_bills(safe_to_spend_client):
    today = date.today()
    account = Account(
        account_id="safe-spend-account",
        user_id="safe-spend-user",
        name="Checking",
        type="depository",
        subtype="checking",
        balance=Decimal("1000.00"),
    )
    scenario = PlanningScenario(name="Monthly plan", account_id=account.account_id)
    transaction = Transaction(
        transaction_id="safe-spend-plaid-outflow",
        account_id=account.account_id,
        user_id=None,
        provider="plaid",
        amount=Decimal("42.50"),
        date=today,
        description="Groceries",
        category="Food",
        is_internal=False,
    )
    manual_expense = Transaction(
        transaction_id="safe-spend-manual-outflow",
        account_id=account.account_id,
        user_id=None,
        provider="manual",
        amount=Decimal("-12.25"),
        date=today,
        description="Cash purchase",
        category="Shopping",
        is_internal=False,
    )
    income_transactions = [
        Transaction(
            transaction_id=f"safe-spend-income-{days_ago}",
            account_id=account.account_id,
            user_id=None,
            provider=provider,
            amount=amount,
            date=today.fromordinal(today.toordinal() - days_ago),
            description="Payroll",
            category="Income",
            is_internal=False,
        )
        for days_ago, provider, amount in (
            (28, "plaid", Decimal("-1500.00")),
            (14, "manual", Decimal("1500.00")),
        )
    ]
    bill = PlannedBill(
        scenario=scenario,
        name="Electricity",
        amount_cents=12_500,
        due_date=today,
        frequency="monthly",
        origin="manual",
        account_id=account.account_id,
        predicted=False,
    )
    db.session.add_all([account, scenario, transaction, manual_expense, *income_transactions, bill])
    db.session.commit()

    response = safe_to_spend_client.get(
        f"/api/dashboard/safe-to-spend?as_of={today.isoformat()}&user_id=safe-spend-user&buffer_cents=0"
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "success"
    assert payload["data"]["components"]["spendable_cash_cents"] == 100_000
    assert payload["data"]["components"]["upcoming_outflows_cents"] == 12_500
    assert payload["data"]["components"]["spent_today_cents"] == 5_475
    assert payload["data"]["next_income_date"] == today.fromordinal(today.toordinal() + 14).isoformat()
    assert [item["name"] for item in payload["data"]["upcoming_bills"]] == ["Electricity"]

    other_user_response = safe_to_spend_client.get(
        f"/api/dashboard/safe-to-spend?as_of={today.isoformat()}&user_id=other-user&buffer_cents=0"
    )
    assert other_user_response.status_code == 200
    other_user_payload = other_user_response.get_json()["data"]
    assert other_user_payload["components"]["spent_today_cents"] == 0
    assert other_user_payload["upcoming_bills"] == []

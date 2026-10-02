"""Real SQL coverage for safe-to-spend provider signs, ownership and route."""

import importlib
import os
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from flask import Flask


@pytest.fixture()
def database():
    """Load real app modules independently of legacy tests' import-time stubs."""
    os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
    saved = {key: value for key, value in sys.modules.items() if key == "app" or key.startswith("app.")}
    for key in saved:
        sys.modules.pop(key)
    try:
        db = importlib.import_module("app.extensions").db
        models = importlib.import_module("app.models")
        service = importlib.import_module("app.services.safe_to_spend")
        route = importlib.import_module("app.routes.dashboard")
        app = Flask(__name__)
        app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", SQLALCHEMY_TRACK_MODIFICATIONS=False)
        db.init_app(app)
        app.register_blueprint(route.dashboard, url_prefix="/api/dashboard")
        with app.app_context():
            db.create_all()
            db.session.add_all(
                [
                    models.Account(account_id="a", user_id="user-a", name="Checking", type="depository", balance=1000),
                    models.Account(account_id="b", user_id="user-b", name="Checking", type="depository", balance=100),
                ]
            )
            db.session.commit()
            yield db, models, service, app.test_client()
            db.session.remove()
            db.drop_all()
    finally:
        for key in list(sys.modules):
            if key == "app" or key.startswith("app."):
                sys.modules.pop(key)
        sys.modules.update(saved)
        sys.path.pop(0)


@pytest.mark.parametrize("provider,expense,income", [("plaid", "42.50", "-1500"), ("manual", "-42.50", "1500")])
def test_provider_signs_and_account_ownership(database, provider, expense, income):
    db, models, service, _ = database
    for txn_id, amount, day in [("expense", expense, 12), ("income-1", income, 1), ("income-2", income, 8)]:
        db.session.add(
            models.Transaction(
                transaction_id=txn_id,
                account_id="a",
                user_id=None,
                provider=provider,
                amount=Decimal(amount),
                date=date(2026, 7, day),
                description="Payroll" if "income" in txn_id else "Shop",
            )
        )
    db.session.commit()
    assert service._spent_between(date(2026, 7, 1), date(2026, 7, 12), "user-a") == 4250
    assert service._spent_between(date(2026, 7, 1), date(2026, 7, 12), "user-b") == 0
    assert service._next_income_date(date(2026, 7, 12), "user-a") == date(2026, 7, 15)
    assert service._next_income_date(date(2026, 7, 12), "user-b") is None


def test_real_safe_to_spend_route(database):
    db, models, _, client = database
    scenario = models.PlanningScenario(name="Budget", account_id="a")
    db.session.add(scenario)
    db.session.flush()
    db.session.add(
        models.PlannedBill(scenario_id=scenario.id, name="Power", amount_cents=15000, due_date=date(2026, 7, 12))
    )
    db.session.add(
        models.Transaction(
            transaction_id="expense",
            account_id="a",
            user_id=None,
            provider="plaid",
            amount=Decimal("42.50"),
            date=date(2026, 7, 12),
            description="Shop",
        )
    )
    db.session.commit()
    response = client.get("/api/dashboard/safe-to-spend?user_id=user-a&as_of=2026-07-12")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "success"
    assert payload["data"]["components"] == {
        "spendable_cash_cents": 100000,
        "upcoming_outflows_cents": 15000,
        "required_buffer_cents": 25000,
        "spent_today_cents": 4250,
    }
    assert payload["data"]["upcoming_bills"][0]["name"] == "Power"

"""Cash-basis Money In / Money Out for funding accounts, kept apart from the economic view."""

import os
import sys
from datetime import date
from decimal import Decimal

import pytest

BASE_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)
os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")

from app.extensions import db  # noqa: E402
from app.models import Account, Transaction  # noqa: E402
from app.routes.charts import charts  # noqa: E402
from app.routes.summary import fetch_transaction_data  # noqa: E402
from app.services import recurring_repository as repo  # noqa: E402
from flask import Flask  # noqa: E402

DAY = date(2026, 10, 13)
RANGE = {"start_date": "2026-10-01", "end_date": "2026-10-31"}


@pytest.fixture()
def app(monkeypatch):
    flask_app = Flask(__name__)
    flask_app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", SQLALCHEMY_TRACK_MODIFICATIONS=False)
    db.init_app(flask_app)
    flask_app.register_blueprint(charts, url_prefix="/api/charts")
    monkeypatch.setenv(repo.OWNER_ENV, "alice")
    with flask_app.app_context():
        db.create_all()
        accounts = (
            ("chk", "alice", "depository", "checking", False),
            ("sav", "alice", "depository", "savings", False),
            ("card", "alice", "credit", "credit card", False),
            ("loan", "alice", "loan", "student", False),
            ("inv", "alice", "investment", "brokerage", False),
            ("hidden", "alice", "depository", "checking", True),
            ("bob-chk", "bob", "depository", "checking", False),
        )
        for account_id, user, kind, sub, hidden in accounts:
            db.session.add(
                Account(account_id=account_id, user_id=user, name=account_id, type=kind, subtype=sub, is_hidden=hidden)
            )
        db.session.commit()
        yield flask_app
        db.session.remove()
        db.drop_all()


def add(txid, account, raw, primary=None, detailed=None, user="alice", **extra):
    """Plaid sign: a positive raw amount is money out of the account."""
    pending = extra.pop("pending", False)
    db.session.add(
        Transaction(
            transaction_id=txid,
            user_id=user,
            account_id=account,
            date=DAY,
            amount=Decimal(str(raw)),
            provider="plaid",
            pending=pending,
            description=extra.pop("description", txid),
            personal_finance_category={"primary": primary, "detailed": detailed or primary} if primary else None,
            **extra,
        )
    )


def cash(client):
    body = client.get("/api/charts/daily_net", query_string=RANGE).get_json()
    day = next((d for d in body["data"] if d["date"] == DAY.isoformat()), None)
    return body, day


def test_card_payment_counts_once_as_cash_and_purchase_once_as_economic(app):
    add("purchase", "card", 400, "GENERAL_MERCHANDISE")
    add("pay-chk", "chk", 600, "LOAN_PAYMENTS", "LOAN_PAYMENTS_CREDIT_CARD_PAYMENT")
    add("pay-card", "card", -600, "LOAN_PAYMENTS", "LOAN_PAYMENTS_CREDIT_CARD_PAYMENT")
    db.session.commit()
    body, day = cash(app.test_client())
    assert day["cash_flow"]["money_out"] == 600.0
    assert day["cash_flow"]["debt_payment_out"] == 600.0
    assert day["cash_flow"]["money_in"] == 0.0  # the card-side credit is not cash in
    assert day["expenses"]["parsedValue"] == -400.0  # purchase-time economic expense only
    assert body["coverage"]["cash_flow"]["complete"] is True


def test_loan_installment_is_cash_out_and_loan_proceeds_are_not_income(app):
    add("installment", "chk", 250, "LOAN_PAYMENTS", "LOAN_PAYMENTS_STUDENT_LOAN_PAYMENT")
    add(
        "proceeds",
        "chk",
        -1000,
        "TRANSFER_IN",
        "TRANSFER_IN_CASH_ADVANCES_AND_LOANS",
    )
    db.session.commit()
    _, day = cash(app.test_client())
    assert day["cash_flow"]["debt_payment_out"] == 250.0
    assert day["cash_flow"]["financing_in"] == 1000.0
    assert day["cash_flow"]["income_in"] == 0.0
    assert day["income"]["parsedValue"] == 0.0


def test_confirmed_own_transfer_is_excluded_from_both_totals(app):
    add(
        "t-out", "chk", 800, "TRANSFER_OUT", "TRANSFER_OUT_ACCOUNT_TRANSFER", is_internal=True, internal_match_id="t-in"
    )
    add("t-in", "sav", -800, "TRANSFER_IN", "TRANSFER_IN_ACCOUNT_TRANSFER", is_internal=True, internal_match_id="t-out")
    db.session.commit()
    _, day = cash(app.test_client())
    cf = day["cash_flow"]
    assert cf["money_out"] == 0.0 and cf["money_in"] == 0.0
    assert cf["verified_own_transfer_out"] == 800.0 and cf["verified_own_transfer_in"] == 800.0


def test_investment_allocation_p2p_and_one_sided_transfer_stay_visible(app):
    add("to-inv", "chk", 300, "TRANSFER_OUT", "TRANSFER_OUT_INVESTMENT_AND_RETIREMENT_FUNDS")
    add("p2p", "chk", 45, "GENERAL_SERVICES", description="Venmo Payment to Sam")
    add("onesided", "chk", 75, "TRANSFER_OUT", "TRANSFER_OUT_ACCOUNT_TRANSFER")
    add("mystery-credit", "chk", -100)
    db.session.commit()
    body, day = cash(app.test_client())
    cf = day["cash_flow"]
    assert cf["investment_allocation_out"] == 300.0
    assert cf["external_person_out"] == 45.0
    assert cf["unclassified_out"] == 75.0  # included in gross outgoing cash, flagged for review
    assert cf["unclassified_in"] == 100.0 and cf["income_in"] == 0.0
    assert cf["money_out"] == 420.0
    assert cf["net_cash"] == -320.0
    assert body["coverage"]["cash_flow"]["needs_review"] is True


def test_unpaired_internal_flag_is_not_silently_excluded(app):
    add("flagged", "chk", 90, "TRANSFER_OUT", "TRANSFER_OUT_ACCOUNT_TRANSFER", is_internal=True)
    db.session.commit()
    body, day = cash(app.test_client())
    assert day["cash_flow"]["unclassified_out"] == 90.0
    assert day["cash_flow"]["verified_own_transfer_out"] == 0.0
    assert body["coverage"]["cash_flow"]["unverified_internal"] == {"count": 1, "cents": 9000}


def test_hidden_pending_and_foreign_owner_do_not_contaminate(app):
    add("ok", "chk", 10, "FOOD_AND_DRINK")
    add("hid", "hidden", 999, "FOOD_AND_DRINK")
    add("pend", "chk", 888, "FOOD_AND_DRINK", pending=True)
    add("bob", "bob-chk", 777, "FOOD_AND_DRINK", user="bob")
    db.session.commit()
    _, day = cash(app.test_client())
    assert day["cash_flow"]["money_out"] == 10.0


def test_no_funding_accounts_reports_incomplete_not_zero_coverage(app):
    add("card-buy", "card", 50, "GENERAL_MERCHANDISE")
    db.session.commit()
    body, day = cash(app.test_client())
    assert body["coverage"]["cash_flow"]["complete"] is False
    assert day["cash_flow"]["money_out"] == 0.0
    assert day["expenses"]["parsedValue"] == -50.0


def test_summary_rows_carry_additive_cash_fields(app):
    add("buy", "chk", 20, "FOOD_AND_DRINK")
    db.session.commit()
    rows = fetch_transaction_data(DAY, DAY, "alice")
    assert rows[0].expenses == 20.0 and rows[0].money_out == 20.0 and rows[0].net_cash == -20.0


def test_diagnostic_explains_gap_without_ledger_text(app):
    add("buy", "card", 400, "GENERAL_MERCHANDISE", description="SECRET MERCHANT")
    add("pay", "chk", 600, "LOAN_PAYMENTS", "LOAN_PAYMENTS_CREDIT_CARD_PAYMENT", description="SECRET MEMO")
    db.session.commit()
    response = app.test_client().get("/api/charts/cash_flow_diagnostic", query_string=RANGE)
    data = response.get_json()["data"]
    assert data["money_out"] == 600.0 and data["economic_expenses"] == 400.0
    assert data["money_out_minus_economic_expenses"] == 200.0
    assert data["components"]["debt_payment_out"] == {"count": 1, "amount": 600.0}
    assert data["non_funding_legs_excluded"]["credit"]["amount"] == 400.0
    assert data["by_account"][0]["months"][0] == {"month": "2026-10", "out": 600.0, "in": 0.0}
    assert "SECRET" not in response.get_data(as_text=True)


def test_diagnostic_requires_dates_and_owner(app, monkeypatch):
    client = app.test_client()
    assert client.get("/api/charts/cash_flow_diagnostic").status_code == 400
    monkeypatch.delenv(repo.OWNER_ENV, raising=False)
    assert client.get("/api/charts/cash_flow_diagnostic", query_string=RANGE).status_code == 503

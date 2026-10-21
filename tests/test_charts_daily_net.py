"""Daily Net and summary use one economic-flow classification, bound to the trusted owner."""

import os
import sys
from datetime import date, timedelta
from decimal import Decimal

import pytest

BASE_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)
os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")

from app.extensions import db  # noqa: E402
from app.models import Account, Transaction  # noqa: E402
from app.routes.charts import charts  # noqa: E402
from app.routes.summary import summary  # noqa: E402
from app.routes.transactions import transactions  # noqa: E402
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
    flask_app.register_blueprint(summary, url_prefix="/api/summary")
    flask_app.register_blueprint(transactions, url_prefix="/api/transactions")
    monkeypatch.setenv(repo.OWNER_ENV, "alice")
    with flask_app.app_context():
        db.create_all()
        accounts = (
            ("chk", "alice", "depository", "checking", False),
            ("sav", "alice", "depository", "savings", False),
            ("card", "alice", "credit", "credit card", False),
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


def add(txid, account, raw, primary=None, detailed=None, user="alice", day=DAY, **extra):
    db.session.add(
        Transaction(
            transaction_id=txid,
            user_id=user,
            account_id=account,
            date=day,
            amount=Decimal(str(raw)),
            provider="plaid",
            description=extra.pop("description", txid),
            personal_finance_category={"primary": primary, "detailed": detailed or primary} if primary else None,
            **extra,
        )
    )


def seed_screenshot_day():
    """+$1000 payroll, a confirmed +$200 own transfer (with its -$200 leg), an unpaired +$100 credit,
    a $40 purchase, a $25 refund, $15 card interest and a $300 card payment."""
    add("payroll", "chk", -1000, "INCOME", "INCOME_WAGES")
    add("z-in", "chk", -200, "TRANSFER_IN", "TRANSFER_IN_ACCOUNT_TRANSFER", is_internal=True, internal_match_id="z-out")
    add(
        "z-out", "sav", 200, "TRANSFER_OUT", "TRANSFER_OUT_ACCOUNT_TRANSFER", is_internal=True, internal_match_id="z-in"
    )
    add("b100", "chk", -100, "TRANSFER_IN", "TRANSFER_IN_ACCOUNT_TRANSFER", description="BANK TRANSFER")
    add("lunch", "chk", 40, "FOOD_AND_DRINK")
    add("refund", "chk", -25, "GENERAL_MERCHANDISE")
    add("apr", "card", 15, "BANK_FEES", "BANK_FEES_INTEREST_CHARGE")
    add("cardpay", "chk", 300, "LOAN_PAYMENTS", "LOAN_PAYMENTS_CREDIT_CARD_PAYMENT")
    db.session.commit()


def daily(client, **params):
    response = client.get("/api/charts/daily_net", query_string={**RANGE, **params})
    return response


def the_day(body):
    return next(d for d in body["data"] if d["date"] == DAY.isoformat())


def test_daily_net_separates_economics_from_account_movement(app):
    seed_screenshot_day()
    body = daily(app.test_client()).get_json()
    day = the_day(body)
    assert day["income"]["parsedValue"] == 1000.0  # payroll only: the +$200 and +$100 are not income
    assert day["expenses"]["parsedValue"] == -55.0  # $40 purchase + $15 card interest
    assert day["refunds"] == 25.0
    assert day["net"]["parsedValue"] == 970.0  # 1000 - 55 + 25
    assert (day["transfer_in"], day["transfer_out"]) == (200.0, 200.0)
    assert day["unclassified_inflows"] == 100.0 and day["unclassified_outflows"] == 0.0
    assert day["debt_settlement"] == 300.0  # paying the card is not a second spending event
    assert day["transfer_count"] == 2 and day["unclassified_count"] == 1
    assert day["transaction_count"] == 6  # confirmed transfers are not activity rows
    # The economic coverage keys are unchanged; the cash-basis block is additive.
    assert {k: v for k, v in body["coverage"].items() if k != "cash_flow"} == {
        "classified_count": 7,
        "unclassified_count": 1,
        "needs_review": True,
        "basis": "economic_flow",
    }
    assert body["coverage"]["cash_flow"]["basis"] == "cash_movement"


def test_the_old_shape_is_preserved_for_existing_chart_consumers(app):
    seed_screenshot_day()
    day = the_day(daily(app.test_client()).get_json())
    for key in ("income", "expenses", "net"):
        assert set(day[key]) == {"source", "parsedValue"}
    assert day["income"]["source"] == "1000.0"
    assert isinstance(day["transaction_count"], int)


def test_nothing_is_mutated_and_repeat_runs_are_identical(app):
    seed_screenshot_day()
    before = {t.transaction_id: (t.amount, t.is_internal, t.internal_match_id) for t in Transaction.query.all()}
    first = daily(app.test_client()).get_json()
    second = daily(app.test_client()).get_json()
    assert first == second
    after = {t.transaction_id: (t.amount, t.is_internal, t.internal_match_id) for t in Transaction.query.all()}
    assert before == after and after["b100"][1] is False  # the unpaired credit was not auto-flagged


def test_other_owners_hidden_accounts_and_pending_rows_are_omitted(app):
    add("mine", "chk", -500, "INCOME", "INCOME_WAGES")
    add("bobs", "bob-chk", -9999, "INCOME", "INCOME_WAGES", user="bob")
    add("bobs-on-mine", "bob-chk", -7777, "INCOME", "INCOME_WAGES", user="alice")  # mismatched account owner
    add("hid", "hidden", -4444, "INCOME", "INCOME_WAGES")
    add("pend", "chk", -3333, "INCOME", "INCOME_WAGES", pending=True)
    add("outside", "chk", -2222, "INCOME", "INCOME_WAGES", day=date(2026, 9, 1))
    db.session.commit()
    day = the_day(daily(app.test_client()).get_json())
    assert day["income"]["parsedValue"] == 500.0 and day["transaction_count"] == 1


def test_fails_closed_without_a_trusted_owner_and_validates_dates(app, monkeypatch):
    seed_screenshot_day()
    monkeypatch.delenv(repo.OWNER_ENV, raising=False)
    response = daily(app.test_client())
    assert response.status_code == 503 and response.get_json()["code"] == "owner_not_configured"
    assert "data" not in response.get_json()
    monkeypatch.setenv(repo.OWNER_ENV, "alice")
    assert daily(app.test_client(), start_date="nope").status_code == 400
    assert daily(app.test_client(), start_date="2026-11-01", end_date="2026-10-01").status_code == 400


def test_chart_and_summary_agree_for_the_same_owner_and_dates(app):
    seed_screenshot_day()
    add("later-pay", "chk", -250, "INCOME", "INCOME_WAGES", day=DAY + timedelta(days=3))
    add("later-buy", "chk", 80, "TRANSPORTATION", day=DAY + timedelta(days=3))
    db.session.commit()
    client = app.test_client()
    chart = daily(client).get_json()["data"]
    stats = client.get("/api/summary/financial", query_string=RANGE).get_json()["data"]
    assert stats["totalIncome"] == round(sum(d["income"]["parsedValue"] for d in chart), 2) == 1250.0
    assert stats["totalExpenses"] == round(-sum(d["expenses"]["parsedValue"] for d in chart), 2) == 135.0
    assert stats["totalRefunds"] == round(sum(d["refunds"] for d in chart), 2) == 25.0
    assert stats["totalNet"] == round(sum(d["net"]["parsedValue"] for d in chart), 2) == 1140.0


def test_summary_fails_closed_without_an_owner(app, monkeypatch):
    seed_screenshot_day()
    monkeypatch.delenv(repo.OWNER_ENV, raising=False)
    response = app.test_client().get("/api/summary/financial", query_string=RANGE)
    assert response.status_code == 503 and response.get_json()["code"] == "owner_not_configured"


# ----------------------------------------------------------------------------- transaction list metadata


def listing(client, **params):
    return client.get("/api/transactions/get_transactions", query_string={"page_size": 50, **params})


def test_listed_rows_carry_the_same_classification_and_hide_transfers_by_default(app):
    seed_screenshot_day()
    body = listing(app.test_client(), **RANGE).get_json()["data"]
    rows = {t["transaction_id"]: t for t in body["transactions"]}
    assert "z-in" not in rows and "z-out" not in rows  # explorer behaviour unchanged by default
    assert rows["payroll"]["reporting_flow_kind"] == "income" and rows["payroll"]["flow_confidence"] == "medium"
    assert rows["b100"]["reporting_flow_kind"] == "unclassified"
    assert rows["b100"]["flow_reason_codes"] == ["pfc_account_transfer_unpaired"]
    assert rows["cardpay"]["reporting_flow_kind"] == "debt_settlement"
    assert rows["refund"]["reporting_flow_kind"] == "refund"


def test_include_transfers_keeps_confirmed_pairs_for_the_daily_modal(app):
    seed_screenshot_day()
    body = listing(app.test_client(), include_transfers="true", **RANGE).get_json()["data"]
    rows = {t["transaction_id"]: t for t in body["transactions"]}
    assert {"z-in", "z-out"} <= set(rows)
    assert rows["z-in"]["reporting_flow_kind"] == "transfer" and rows["z-in"]["flow_reason_codes"] == [
        "confirmed_internal"
    ]
    assert body["total"] == len(rows)


def test_include_transfers_is_owner_bound_and_fails_closed(app, monkeypatch):
    seed_screenshot_day()
    add("bob-row", "bob-chk", -5, user="bob")
    db.session.commit()
    rows = listing(app.test_client(), include_transfers="true", **RANGE).get_json()["data"]["transactions"]
    assert "bob-row" not in {t["transaction_id"] for t in rows}
    monkeypatch.delenv(repo.OWNER_ENV, raising=False)
    response = listing(app.test_client(), include_transfers="true", **RANGE)
    assert response.status_code == 503 and response.get_json()["code"] == "owner_not_configured"
    assert listing(app.test_client(), **RANGE).status_code == 200  # the plain explorer keeps working


def test_row_economic_amounts_reconcile_with_the_daily_net_buckets(app):
    """The modal's rows and the chart's day bucket come from one classifier and must add up."""
    seed_screenshot_day()
    client = app.test_client()
    day = {d["date"]: d for d in daily(client).get_json()["data"]}
    rows = listing(client, include_transfers="true", **RANGE).get_json()["data"]["transactions"]
    for date_key, bucket in day.items():
        mine = [t for t in rows if t["date"] == date_key]

        def total(kind, field="economic_amount"):
            return round(sum(t[field] or 0 for t in mine if t["reporting_flow_kind"] == kind), 2)

        assert total("income") == bucket["income"]["parsedValue"]
        assert total("expense") == bucket["expenses"]["parsedValue"]
        assert total("refund") == bucket["refunds"]
        assert round(total("income") + total("expense") + total("refund"), 2) == bucket["net"]["parsedValue"]
        assert sum(1 for t in mine if t["reporting_flow_kind"] == "transfer") == bucket["transfer_count"]
        assert sum(1 for t in mine if t["reporting_flow_kind"] == "unclassified") == bucket["unclassified_count"]
        assert all(
            t["economic_amount"] is None for t in mine if t["reporting_flow_kind"] in {"transfer", "debt_settlement"}
        )

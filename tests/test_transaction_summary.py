"""Filtered Activity table totals: all matching rows, one filter owner, economic vs movement."""

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
from app.routes.transactions import transactions  # noqa: E402
from app.services import recurring_repository as repo  # noqa: E402
from flask import Flask  # noqa: E402

DAY = date(2026, 10, 13)


@pytest.fixture()
def app(monkeypatch):
    flask_app = Flask(__name__)
    flask_app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", SQLALCHEMY_TRACK_MODIFICATIONS=False)
    db.init_app(flask_app)
    flask_app.register_blueprint(transactions, url_prefix="/api/transactions")
    monkeypatch.setenv(repo.OWNER_ENV, "alice")
    with flask_app.app_context():
        db.create_all()
        for account_id, user, kind, sub, hidden in (
            ("chk", "alice", "depository", "checking", False),
            ("sav", "alice", "depository", "savings", False),
            ("card", "alice", "credit", "credit card", False),
            ("hid", "alice", "depository", "checking", True),
            ("bob-chk", "bob", "depository", "checking", False),
        ):
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
            category=extra.pop("category", "Food" if primary else None),
            personal_finance_category={"primary": primary, "detailed": detailed or primary} if primary else None,
            **extra,
        )
    )


def seed_economic():
    add("pay", "chk", -1000, "INCOME", "INCOME_WAGES", category="Income")
    add("rent", "chk", 300, "RENT_AND_UTILITIES", category="Rent")
    add("refund", "chk", -25, "GENERAL_MERCHANDISE", category="Shopping")
    add("t-in", "chk", -200, "TRANSFER_IN", "TRANSFER_IN_ACCOUNT_TRANSFER", is_internal=True, internal_match_id="t-out")
    add(
        "t-out", "sav", 200, "TRANSFER_OUT", "TRANSFER_OUT_ACCOUNT_TRANSFER", is_internal=True, internal_match_id="t-in"
    )
    add("cc", "chk", 131.64, "LOAN_PAYMENTS", "LOAN_PAYMENTS_CREDIT_CARD_PAYMENT", category="Credit card payment")
    add("mystery", "chk", -100)
    # Never part of the aggregate: someone else's data, a hidden account and a pending row.
    add("bob", "bob-chk", 999, "FOOD_AND_DRINK", user="bob")
    add("hidden", "hid", 777, "FOOD_AND_DRINK")
    add("pending", "chk", 55, "FOOD_AND_DRINK", pending=True)
    db.session.commit()


def get(client, path="/api/transactions/summary", **params):
    response = client.get(path, query_string=params)
    return response.status_code, response.get_json()


def test_economic_fixture_separates_movement_and_review(app):
    seed_economic()
    status, body = get(app.test_client(), include_transfers="true")
    data = body["data"]
    assert status == 200 and data["scope"] == "all_matching"
    assert data["income"] == 1000 and data["expenses"] == -300 and data["refunds"] == 25
    assert data["economic_net"] == 725
    assert data["transfers_in"] == 200 and data["transfers_out"] == 200
    assert data["debt_settlements"] == 131.64
    assert data["unclassified_in"] == 100 and data["needs_review_count"] == 1
    assert data["pending_excluded_count"] == 1
    assert data["matching_count"] == 7  # owner, visible, posted rows only


def test_default_view_keeps_table_transfer_semantics(app):
    seed_economic()
    _, body = get(app.test_client())
    data = body["data"]
    assert data["transfers_in"] == 0 and data["transfers_out"] == 0
    assert data["matching_count"] == 5
    assert data["economic_net"] == 725


def test_breakdowns_reconcile_to_headline(app):
    seed_economic()
    _, body = get(app.test_client(), include_transfers="true")
    data = body["data"]
    for key in ("by_category", "by_account", "by_month"):
        rows = data["breakdowns"][key]
        assert round(sum(r["economic_net"] for r in rows), 2) == data["economic_net"]
        assert round(sum(r["income"] for r in rows), 2) == data["income"]
        assert round(sum(r["expenses"] for r in rows), 2) == data["expenses"]
    assert {r["key"] for r in data["breakdowns"]["by_month"]} == {"2026-10"}


def test_owner_missing_fails_closed(app, monkeypatch):
    monkeypatch.delenv(repo.OWNER_ENV, raising=False)
    status, body = get(app.test_client())
    assert status == 503 and body["status"] == "error"


def test_bad_date_is_400(app):
    status, _ = get(app.test_client(), start_date="nope")
    assert status == 400


def test_empty_match_is_zeroes_not_errors(app):
    seed_economic()
    status, body = get(app.test_client(), search="no-such-thing")
    data = body["data"]
    assert status == 200 and data["matching_count"] == 0
    assert data["economic_net"] == 0 and data["breakdowns"]["by_category"] == []


def test_51_rows_summary_ignores_page_and_sort_and_matches_table(app):
    for index in range(51):
        add(f"r{index:02d}", "chk", 10 + index, "FOOD_AND_DRINK", day=DAY - timedelta(days=index % 20))
    db.session.commit()
    client = app.test_client()
    expected = -sum(10 + i for i in range(51))
    _, summary = get(client)
    assert summary["data"]["matching_count"] == 51 and summary["data"]["expenses"] == expected
    for page, sort in ((1, "date_desc"), (2, "amount_desc"), (4, "merchant_asc")):
        _, table = get(client, "/api/transactions/get_transactions", page=page, page_size=15, sort=sort)
        assert table["data"]["total"] == 51
    _, page4 = get(client, "/api/transactions/get_transactions", page=4, page_size=15)
    assert len(page4["data"]["transactions"]) == 6


def test_search_and_field_filters_narrow_count_and_summary_identically(app):
    add("a1", "chk", 10, "FOOD_AND_DRINK", description="Cafe Uno", merchant_name="Cafe Uno", category="Food: Coffee")
    add("a2", "chk", 20, "FOOD_AND_DRINK", description="Cafe Dos", merchant_name="Cafe Dos", category="Food: Coffee")
    add("a3", "sav", 30, "RENT_AND_UTILITIES", description="Landlord", category="Rent: Housing")
    add("a4", "chk", 5, "FOOD_AND_DRINK", description="100% juice", category="Food: Drinks")
    db.session.commit()
    client = app.test_client()
    cases = [
        ({"search": "cafe"}, 2, -30),
        ({"search": "CAFE UNO"}, 1, -10),
        ({"filter_category": "coffee"}, 2, -30),
        ({"category_primary": "food", "category_sub": "drinks"}, 1, -5),
        ({"filter_account_name": "sav"}, 1, -30),
        ({"filter_merchant_name": "dos", "search": "cafe"}, 1, -20),
        ({"search": "100%"}, 1, -5),  # LIKE wildcards are literal
        ({"search": "%"}, 1, -5),
        ({"search": "_"}, 0, 0),
        ({"filter_date": "2026-10-13"}, 4, -65),
    ]
    for params, count, expenses in cases:
        _, table = get(client, "/api/transactions/get_transactions", page_size=50, **params)
        _, summary = get(client, **params)
        assert table["data"]["total"] == count, params
        assert summary["data"]["matching_count"] == count, params
        assert summary["data"]["expenses"] == expenses, params
        assert summary["data"]["applied_filters"], params


def test_account_and_type_filters(app):
    seed_economic()
    client = app.test_client()
    _, body = get(client, account_ids="sav", include_transfers="true")
    assert body["data"]["matching_count"] == 1 and body["data"]["transfers_out"] == 200
    # ``tx_type`` keeps the table's raw stored-sign semantics (Plaid: positive = money out).
    _, positive = get(client, tx_type="credit")
    assert positive["data"]["matching_count"] == 2  # rent and the card payment
    _, negative = get(client, tx_type="debit")
    assert negative["data"]["matching_count"] == 3  # payroll, refund, unclassified

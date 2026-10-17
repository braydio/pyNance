"""Transaction insights: totals over every matching row, review items, scope and caching."""

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
from app.models import Account, RecurringStream, Transaction  # noqa: E402
from app.routes.transactions import transactions  # noqa: E402
from app.services import recurring_repository as repo  # noqa: E402
from app.services import transaction_insights as insights  # noqa: E402
from flask import Flask  # noqa: E402

TODAY = date(2026, 10, 17)
RANGE = {"start_date": "2026-10-01", "end_date": "2026-10-31"}
DAY = date(2026, 10, 13)


@pytest.fixture()
def app(monkeypatch):
    insights.invalidate_insights_cache()
    flask_app = Flask(__name__)
    flask_app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", SQLALCHEMY_TRACK_MODIFICATIONS=False)
    db.init_app(flask_app)
    flask_app.register_blueprint(transactions, url_prefix="/api/transactions")
    monkeypatch.setenv(repo.OWNER_ENV, "alice")
    with flask_app.app_context():
        db.create_all()
        for account_id, user, kind, sub in (
            ("chk", "alice", "depository", "checking"),
            ("sav", "alice", "depository", "savings"),
            ("card", "alice", "credit", "credit card"),
            ("bob-chk", "bob", "depository", "checking"),
        ):
            db.session.add(Account(account_id=account_id, user_id=user, name=account_id, type=kind, subtype=sub))
        db.session.commit()
        yield flask_app
        db.session.remove()
        db.drop_all()
    insights.invalidate_insights_cache()


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


def seed():
    add("pay", "chk", -3000, "INCOME", "INCOME_WAGES", category="Income")
    add("rent", "chk", 1200, "RENT_AND_UTILITIES", category="Rent")
    add("lunch1", "card", 18, "FOOD_AND_DRINK", merchant_name="Cafe Uno")
    add("lunch2", "card", 18, "FOOD_AND_DRINK", merchant_name="Cafe Uno")  # same account, merchant, amount, day
    add("refund", "chk", -25, "GENERAL_MERCHANDISE", category="Shopping")
    add("fee", "chk", 12, "BANK_FEES", "BANK_FEES_OTHER_BANK_FEES", category="Fees")
    add("apr", "card", 9, "BANK_FEES", "BANK_FEES_INTEREST_CHARGE", category="Fees")
    add("z-in", "chk", -200, "TRANSFER_IN", "TRANSFER_IN_ACCOUNT_TRANSFER", is_internal=True, internal_match_id="z-out")
    add(
        "z-out", "sav", 200, "TRANSFER_OUT", "TRANSFER_OUT_ACCOUNT_TRANSFER", is_internal=True, internal_match_id="z-in"
    )
    add(
        "b100",
        "chk",
        -100,
        "TRANSFER_IN",
        "TRANSFER_IN_ACCOUNT_TRANSFER",
        description="BANK TRANSFER",
        category="Transfer",
    )
    add("mystery", "chk", 33, None, category=None)  # no category at all
    add("cardpay", "chk", 300, "LOAN_PAYMENTS", "LOAN_PAYMENTS_CREDIT_CARD_PAYMENT", category="Payments")
    db.session.commit()


def get(client, path="insights", **params):
    return client.get(f"/api/transactions/{path}", query_string={**RANGE, **params})


def test_numbers_cover_every_matching_row_and_separate_economics_from_movement(app):
    seed()
    data = get(app.test_client()).get_json()["data"]
    assert data["gross_spend"] == 1200 + 18 + 18 + 12 + 9 + 33  # rent, lunches, fee, interest, uncategorized debit
    assert data["refunds"] == 25.0 and data["net_spend"] == data["gross_spend"] - 25.0
    assert data["income"] == 3000.0  # payroll only
    inflow = data["inflow"]
    assert inflow["economic_income"] == 3000.0
    assert inflow["all_credit_movements"] == 3325.0  # payroll 3000 + refund 25 + own transfer 200 + unpaired 100
    assert inflow["transfers_in"] == 200.0 and inflow["unclassified_in"] == 100.0 and inflow["refunds"] == 25.0
    assert (
        inflow["all_credit_movements"] >= inflow["economic_income"] + inflow["transfers_in"] + inflow["unclassified_in"]
    )
    assert data["fees"] == 21.0
    assert data["matching_count"] == 10  # confirmed transfers are not activity rows; nothing is paginated
    assert data["coverage"]["basis"] == "economic_flow" and data["coverage"]["truncated"] is False


def test_the_oct_13_credits_are_not_300_of_income(app):
    add("z200", "chk", -200, "TRANSFER_IN", "TRANSFER_IN_ACCOUNT_TRANSFER", is_internal=True)
    add("b100", "chk", -100, "TRANSFER_IN", "TRANSFER_IN_ACCOUNT_TRANSFER")
    db.session.commit()
    data = get(app.test_client()).get_json()["data"]
    assert data["income"] == 0.0 and data["inflow"]["economic_income"] == 0.0
    assert data["inflow"]["transfers_in"] == 200.0 and data["inflow"]["unclassified_in"] == 100.0


def test_review_items_are_defensible_labelled_and_capped(app):
    seed()
    data = get(app.test_client()).get_json()["data"]
    kinds = {i["kind"]: i for i in data["review_items"]}
    assert set(kinds) == {
        "transfer_candidate",
        "possible_duplicate_same_merchant_amount_day",
        "bank_fee",
        "missing_category",
    }
    dup = kinds["possible_duplicate_same_merchant_amount_day"]
    assert dup["explanation"].startswith("Possible duplicate")  # never claims a duplicate
    assert dup["count"] == 2 and set(dup["transaction_ids"]) == {"lunch1", "lunch2"}
    assert dup["evidence"] == ["Same account", "Same merchant", "Same amount", "Same day"]
    assert kinds["bank_fee"]["count"] == 2 and kinds["bank_fee"]["amount_total"] == 21.0
    assert kinds["missing_category"]["transaction_ids"] == ["mystery"]
    assert kinds["transfer_candidate"]["transaction_ids"] == ["b100"]
    priorities = [i["priority"] for i in data["review_items"]]
    assert priorities == sorted(priorities)
    assert data["uncategorized_count"] == 1


def test_at_most_twenty_review_items_and_ten_ids_each(app):
    for i in range(30):
        add(f"a{i}", "chk", 5, "FOOD_AND_DRINK", merchant_name=f"Shop {i}", day=DAY + timedelta(days=i % 15))
        add(f"b{i}", "chk", 5, "FOOD_AND_DRINK", merchant_name=f"Shop {i}", day=DAY + timedelta(days=i % 15))
    db.session.commit()
    items = get(app.test_client()).get_json()["data"]["review_items"]
    assert len(items) == 20
    assert all(len(i["transaction_ids"]) <= 10 for i in items)


def test_scope_other_owners_accounts_and_categories_are_respected(app):
    seed()
    add("bobs", "bob-chk", 9999, "GENERAL_MERCHANDISE", user="bob")
    db.session.commit()
    client = app.test_client()
    everything = get(client).get_json()["data"]
    assert everything["gross_spend"] < 9000  # bob's purchase never leaks in
    only_card = get(client, account_ids="card").get_json()["data"]
    assert only_card["gross_spend"] == 18 + 18 + 9 and only_card["matching_count"] == 3
    assert get(client, account_ids="bob-chk").get_json()["data"]["matching_count"] == 0
    food = get(client, category="Food").get_json()["data"]
    assert food["gross_spend"] == 36.0  # the two lunches: only rows in that category


def test_validation_and_fail_closed(app, monkeypatch):
    seed()
    client = app.test_client()
    assert get(client, start_date="nope").status_code == 400
    assert get(client, start_date="2026-12-01", end_date="2026-10-01").status_code == 400
    assert get(client, start_date="2025-01-01", end_date="2026-10-31").status_code == 400  # > 366 days
    monkeypatch.delenv(repo.OWNER_ENV, raising=False)
    response = get(client)
    assert response.status_code == 503 and response.get_json()["code"] == "owner_not_configured"
    assert "data" not in response.get_json()


def test_counts_use_unified_recurring_and_transfer_sources_and_never_mutate(app):
    seed()
    add(
        "out",
        "chk",
        75,
        "TRANSFER_OUT",
        "TRANSFER_OUT_ACCOUNT_TRANSFER",
        description="Transfer to savings",
        day=DAY + timedelta(days=1),
    )
    add(
        "in",
        "sav",
        -75,
        "TRANSFER_IN",
        "TRANSFER_IN_ACCOUNT_TRANSFER",
        description="Transfer from checking",
        day=DAY + timedelta(days=1),
    )
    repo.create_manual(
        "alice", account_id="chk", display_name="Duke", amount_cash_delta="-80", cadence="monthly",
        anchor_date="2026-11-03", status="proposed", source="detected",
    )  # fmt: skip
    before = {t.transaction_id: (t.amount, t.is_internal) for t in Transaction.query.all()}
    data = get(app.test_client()).get_json()["data"]
    assert data["recurring_candidate_count"] == 1 and RecurringStream.query.count() == 1
    assert data["transfer_pair_count"] == 1
    assert before == {t.transaction_id: (t.amount, t.is_internal) for t in Transaction.query.all()}


def test_results_are_cached_per_owner_and_filters_and_refreshable_and_invalidated(app):
    seed()
    client = app.test_client()
    first = get(client).get_json()["data"]
    assert first["cache"] == {"hit": False}
    add("late", "chk", 500, "GENERAL_MERCHANDISE")
    db.session.commit()
    cached = get(client).get_json()["data"]
    assert cached["cache"] == {"hit": True} and cached["gross_spend"] == first["gross_spend"]
    assert get(client, refresh="true").get_json()["data"]["gross_spend"] == first["gross_spend"] + 500
    add("later", "chk", 1, "GENERAL_MERCHANDISE")
    db.session.commit()
    from app.sql import account_logic

    account_logic.invalidate_tx_cache()  # an edit or refresh drops the insights too
    assert get(client).get_json()["data"]["cache"] == {"hit": False}


# ----------------------------------------------------------------------------- server-side sorting


def listing(client, **params):
    return client.get("/api/transactions/get_transactions", query_string={"page_size": 50, **RANGE, **params})


def test_sort_orders_every_matching_row_server_side(app):
    add("small", "chk", 5, "FOOD_AND_DRINK", merchant_name="Zed", category="B", day=DAY)
    add("big", "chk", 500, "GENERAL_MERCHANDISE", merchant_name="Alpha", category="C", day=DAY - timedelta(days=5))
    add("credit", "chk", -900, "INCOME", "INCOME_WAGES", merchant_name="Mid", category="A", day=DAY - timedelta(days=2))
    db.session.commit()
    client = app.test_client()

    def ids(sort):
        body = listing(client, sort=sort).get_json()["data"]["transactions"]
        return [t["transaction_id"] for t in body]

    assert ids("date_desc") == ["small", "credit", "big"]
    assert ids("date_asc") == ["big", "credit", "small"]
    assert ids("spend_desc")[0] == "big" and ids("spend_desc")[-1] == "credit"  # credits sink
    assert ids("amount_desc") == ["credit", "big", "small"]
    assert ids("merchant_asc") == ["big", "credit", "small"]
    assert ids("category_asc") == ["credit", "small", "big"]
    assert listing(client, sort="bogus").status_code == 400
    assert ids("") == ids("date_desc")

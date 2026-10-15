"""Tests for the account balance/limit/freshness contract and portfolio metrics."""

import os
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest
from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)

os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")

from app.extensions import db  # noqa: E402
from app.models import Account  # noqa: E402
from app.services.account_portfolio_metrics import (  # noqa: E402
    classify_account_group,
    compute_account_metrics,
)
from app.sql.account_logic import (  # noqa: E402
    extract_balance_fields,
    normalize_balance,
    upsert_accounts,
)


@pytest.fixture()
def app_context():
    app = Flask(__name__)
    app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", SQLALCHEMY_TRACK_MODIFICATIONS=False)
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def _payload(account_id="a1", type_="credit", **balances):
    return {
        "account_id": account_id,
        "name": "Card",
        "type": type_,
        "subtype": "credit card",
        "mask": "1234",
        "institution_name": "Bank",
        "balances": balances,
    }


def _acct(**overrides):
    base = {
        "account_id": "x",
        "type": "credit",
        "is_investment": False,
        "balance": Decimal("0"),
        "credit_limit": None,
        "available_balance": None,
        "balance_as_of": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


# --- ingestion -------------------------------------------------------------


def test_valid_zero_balance_is_kept_not_treated_as_missing(app_context):
    upsert_accounts("u1", [_payload(current=0, limit=5000, available=5000)], "plaid")
    account = db.session.get(Account, "a1")
    assert account.balance == Decimal("0.00")
    assert account.balance_as_of is not None
    assert account.credit_limit == Decimal("5000.00")
    assert account.available_balance == Decimal("5000.00")
    assert account.mask == "1234"


def test_missing_current_does_not_overwrite_or_invent_balance(app_context):
    upsert_accounts("u1", [_payload(current=250.5, limit=1000)], "plaid")
    first = db.session.get(Account, "a1")
    as_of = first.balance_as_of

    upsert_accounts("u1", [_payload()], "plaid")  # provider omitted everything
    account = db.session.get(Account, "a1")
    assert account.balance == Decimal("250.50")
    assert account.credit_limit == Decimal("1000.00")  # absent data preserves stored data
    assert account.balance_as_of == as_of


def test_new_account_without_balance_has_unknown_freshness(app_context):
    upsert_accounts("u1", [_payload()], "plaid")
    account = db.session.get(Account, "a1")
    assert account.balance_as_of is None
    assert account.credit_limit is None
    assert compute_account_metrics(account)["balance_status"] == "unknown"


def test_overdraft_limit_on_checking_is_not_a_credit_line(app_context):
    upsert_accounts("u1", [_payload("chk", "depository", current=10, limit=500)], "plaid")
    assert db.session.get(Account, "chk").credit_limit is None


def test_extract_balance_fields_handles_legacy_scalar_and_nulls():
    fields = extract_balance_fields({"balance": 12.5, "type": "depository"})
    assert fields["current"] == Decimal("12.50")
    assert fields["available"] is None and fields["credit_limit"] is None
    assert extract_balance_fields({"balances": {"current": None}})["current"] is None


def test_liability_sign_is_applied_once():
    owed = normalize_balance(Decimal("300"), "credit")
    assert owed == Decimal("300.00")
    assert normalize_balance(owed, "credit") == owed  # idempotent
    assert normalize_balance(Decimal("300"), "credit card") == Decimal("300.00")
    assert normalize_balance(Decimal("-40"), "credit") == Decimal("-40.00")  # overpaid stays a credit
    assert normalize_balance(Decimal("1000"), "loan") == Decimal("1000.00")


# --- metrics ---------------------------------------------------------------


def test_group_classification():
    assert classify_account_group(_acct(type="depository")) == "depository"
    assert classify_account_group(_acct(type="credit")) == "credit"
    assert classify_account_group(_acct(type="loan")) == "loan"
    assert classify_account_group(_acct(type="brokerage", is_investment=True)) == "investment"
    assert classify_account_group(_acct(type="other")) == "other"


def test_card_utilization_and_derived_headroom_are_labelled():
    m = compute_account_metrics(_acct(balance=Decimal("250"), credit_limit=Decimal("1000")))
    assert m["owed"] == Decimal("250")
    assert m["signed_balance"] == Decimal("-250.00")
    assert m["utilization_pct"] == 25.0
    assert m["overlimit"] is False
    assert m["available_credit"] == Decimal("750")
    assert m["available_credit_source"] == "derived"


def test_provider_available_credit_wins_over_derived():
    m = compute_account_metrics(
        _acct(balance=Decimal("250"), credit_limit=Decimal("1000"), available_balance=Decimal("700"))
    )
    assert (m["available_credit"], m["available_credit_source"]) == (Decimal("700"), "provider")


def test_missing_limit_gives_null_not_zero():
    m = compute_account_metrics(_acct(balance=Decimal("250")))
    assert m["utilization_pct"] is None and m["overlimit"] is None
    assert m["available_credit"] is None and m["available_credit_source"] is None
    zero = compute_account_metrics(_acct(balance=Decimal("250"), credit_limit=Decimal("0")))
    assert zero["utilization_pct"] is None


def test_overlimit_is_explicit_and_headroom_not_negative():
    m = compute_account_metrics(_acct(balance=Decimal("1200"), credit_limit=Decimal("1000")))
    assert m["overlimit"] is True
    assert m["utilization_pct"] == 120.0
    assert m["available_credit"] == Decimal("0")


def test_negative_credit_balance_refund_is_zero_owed():
    m = compute_account_metrics(_acct(balance=Decimal("-40"), credit_limit=Decimal("1000")))
    assert m["owed"] == Decimal("0")
    assert m["utilization_pct"] == 0.0


def test_loan_and_investment_have_no_card_metrics():
    loan = compute_account_metrics(_acct(type="loan", balance=Decimal("5000"), credit_limit=Decimal("9")))
    assert loan["group"] == "loan" and loan["owed"] == Decimal("5000")
    assert loan["utilization_pct"] is None and loan["credit_limit"] is None
    inv = compute_account_metrics(_acct(type="brokerage", is_investment=True, balance=Decimal("100")))
    assert inv["owed"] is None and inv["signed_balance"] == Decimal("100.00")


def test_freshness_status():
    now = datetime(2026, 10, 14, tzinfo=timezone.utc)
    fresh = compute_account_metrics(_acct(balance_as_of=now - timedelta(hours=2)), now=now)
    stale = compute_account_metrics(_acct(balance_as_of=now - timedelta(days=5)), now=now)
    assert fresh["balance_status"] == "fresh" and stale["balance_status"] == "stale"


# --- API serialization -----------------------------------------------------


def test_list_accounts_serializes_new_nullable_fields(app_context):
    from app.routes.accounts import accounts as accounts_bp

    app_context.register_blueprint(accounts_bp, url_prefix="/api/accounts")
    upsert_accounts("u1", [_payload(current=100, limit=2000, available=1900)], "plaid")
    upsert_accounts("u1", [_payload("a2", "depository", current=5)], "plaid")

    body = app_context.test_client().get("/api/accounts/get_accounts").get_json()
    rows = {row["account_id"]: row for row in body["accounts"]}
    card, checking = rows["a1"], rows["a2"]
    assert card["credit_limit"] == 2000.0 and card["limit"] == 2000.0
    assert card["available_balance"] == 1900.0
    assert card["mask"] == "1234" and card["balance_as_of"]
    assert card["account_type"] == "credit" and card["is_investment"] is False
    assert checking["credit_limit"] is None and checking["limit"] is None
    assert "access_token" not in card

"""Tests for the optional Plaid Liabilities enrichment adapter."""

import json
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)

os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")

from app.extensions import db  # noqa: E402
from app.models import Account, PlaidAccount  # noqa: E402
from app.services import plaid_liabilities  # noqa: E402
from app.services.plaid_liabilities import parse_liabilities, refresh_item_liabilities  # noqa: E402

NOW = datetime(2026, 10, 14, tzinfo=timezone.utc)


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


def add_account(account_id, type_="credit", item_id="item-1", user_id="u1", subtype="credit card"):
    db.session.add(Account(account_id=account_id, user_id=user_id, name=account_id, type=type_, subtype=subtype))
    db.session.add(PlaidAccount(account_id=account_id, item_id=item_id, access_token="tok"))
    db.session.commit()


def card(account_id, aprs, **extra):
    return {
        "account_id": account_id,
        "aprs": aprs,
        "minimum_payment_amount": 35.0,
        "next_payment_due_date": "2026-11-01",
        "last_statement_balance": 410.25,
        "last_statement_issue_date": "2026-10-05",
        **extra,
    }


def apr(kind, pct):
    return {"apr_type": kind, "apr_percentage": pct, "balance_subject_to_apr": 100.0, "interest_charge_amount": 1.5}


@pytest.fixture()
def remote(monkeypatch):
    calls = []
    state = {"payload": {"liabilities": {}}, "error": None}

    def fake(access_token):
        calls.append(access_token)
        if state["error"]:
            raise state["error"]
        return state["payload"]

    monkeypatch.setattr(plaid_liabilities, "request_liabilities", fake)
    return calls, state


class PlaidErr(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.body = json.dumps({"error_code": code, "error_message": code.lower()})


def test_eligible_card_gets_purchase_apr_buckets_and_payment_metadata(app_context, remote):
    calls, state = remote
    add_account("c1")
    state["payload"] = {"liabilities": {"credit": [card("c1", [apr("purchase_apr", 24.99), apr("cash_apr", 29.99)])]}}

    result = refresh_item_liabilities("item-1", "tok", products={"transactions", "liabilities"}, now=NOW)

    assert result["status"] == "ok" and result["updated"] == ["c1"]
    account = db.session.get(Account, "c1")
    assert account.apr == Decimal("24.99") and account.apr_source == "provider"
    assert account.apr_details["cash_apr"][0]["apr_percentage"] == 29.99  # not collapsed into purchase
    assert account.minimum_payment_amount == Decimal("35.00")
    assert str(account.next_payment_due_date) == "2026-11-01"
    assert account.statement_balance == Decimal("410.25") and str(account.statement_date) == "2026-10-05"
    assert account.liabilities_status == "ok" and account.liabilities_as_of is not None


def test_scope_not_enabled_makes_no_remote_call(app_context, remote):
    calls, _ = remote
    add_account("c1")
    result = refresh_item_liabilities("item-1", "tok", products={"transactions"})
    assert result == {"status": "skipped", "reason": "scope_not_enabled"} and calls == []


def test_empty_apr_list_is_not_a_zero_rate(app_context, remote):
    _, state = remote
    add_account("c1")
    state["payload"] = {"liabilities": {"credit": [card("c1", [])]}}
    refresh_item_liabilities("item-1", "tok", products={"liabilities"}, now=NOW)
    account = db.session.get(Account, "c1")
    assert account.apr is None and account.liabilities_status == "no_rates_reported"
    assert account.minimum_payment_amount == Decimal("35.00")


def test_ambiguous_purchase_aprs_stay_in_details_only(app_context, remote):
    _, state = remote
    add_account("c1")
    state["payload"] = {"liabilities": {"credit": [card("c1", [apr("purchase_apr", 0.0), apr("purchase_apr", 24.99)])]}}
    refresh_item_liabilities("item-1", "tok", products={"liabilities"}, now=NOW)
    account = db.session.get(Account, "c1")
    assert account.apr is None
    assert len(account.apr_details["purchase_apr"]) == 2


def test_loan_rate_is_separate_from_card_apr(app_context, remote):
    _, state = remote
    add_account("l1", type_="loan", subtype="student")
    state["payload"] = {
        "liabilities": {
            "student": [
                {
                    "account_id": "l1",
                    "interest_rate_percentage": 5.5,
                    "minimum_payment_amount": 120.0,
                    "next_payment_due_date": "2026-11-15",
                }
            ]
        }
    }
    refresh_item_liabilities("item-1", "tok", products={"liabilities"}, now=NOW)
    account = db.session.get(Account, "l1")
    assert account.apr is None  # only a genuine card purchase APR populates apr
    assert account.apr_details["loan_interest_rate"]["percentage"] == 5.5
    assert account.minimum_payment_amount == Decimal("120.00")


def test_same_item_two_accounts_use_one_remote_call(app_context, remote):
    calls, state = remote
    add_account("c1")
    add_account("c2")
    state["payload"] = {
        "liabilities": {"credit": [card("c1", [apr("purchase_apr", 20.0)]), card("c2", [apr("purchase_apr", 18.0)])]}
    }
    result = refresh_item_liabilities("item-1", "tok", products={"liabilities"}, now=NOW)
    assert len(calls) == 1 and sorted(result["updated"]) == ["c1", "c2"]


def test_cross_item_and_cross_owner_accounts_are_rejected(app_context, remote):
    _, state = remote
    add_account("c1")
    add_account("other-item", item_id="item-2")
    add_account("other-owner", user_id="u2")
    state["payload"] = {
        "liabilities": {
            "credit": [
                card("c1", [apr("purchase_apr", 20.0)]),
                card("other-item", [apr("purchase_apr", 99.0)]),
                card("other-owner", [apr("purchase_apr", 98.0)]),
                card("ghost", [apr("purchase_apr", 97.0)]),
            ]
        }
    }
    result = refresh_item_liabilities("item-1", "tok", products={"liabilities"}, now=NOW, owner_user_id="u1")
    assert result["updated"] == ["c1"]
    assert set(result["rejected"]) == {"other-item", "other-owner", "ghost"}
    assert db.session.get(Account, "other-item").apr is None
    assert db.session.get(Account, "other-owner").apr is None


def test_consent_unavailable_is_marked_without_raising_or_zeroing(app_context, remote):
    _, state = remote
    add_account("c1")
    state["error"] = PlaidErr("ADDITIONAL_CONSENT_REQUIRED")
    result = refresh_item_liabilities("item-1", "tok", products={"liabilities"}, now=NOW)
    assert result["status"] == "unavailable"
    account = db.session.get(Account, "c1")
    assert account.liabilities_status == "unavailable" and account.apr is None


def test_reauth_failure_reports_reauth_and_keeps_old_data_as_stale(app_context, remote):
    _, state = remote
    add_account("c1")
    state["payload"] = {"liabilities": {"credit": [card("c1", [apr("purchase_apr", 21.0)])]}}
    refresh_item_liabilities("item-1", "tok", products={"liabilities"}, now=NOW)

    state["error"] = PlaidErr("ITEM_LOGIN_REQUIRED")
    result = refresh_item_liabilities("item-1", "tok", products={"liabilities"}, now=NOW)
    assert result["status"] == "error" and result["reauth"] is True
    account = db.session.get(Account, "c1")
    assert account.liabilities_status == "stale" and account.apr == Decimal("21.0000")


def test_provider_apr_replaces_estimated_but_unknown_products_are_ignored():
    parsed = parse_liabilities(
        {"liabilities": {"unknown_product": [{"account_id": "x"}], "credit": [card("c1", [apr("special", 0.0)])]}}
    )
    assert set(parsed) == {"c1"} and parsed["c1"]["buckets"]["special"][0]["apr_percentage"] == 0.0


def test_list_accounts_serializes_liabilities_fields(app_context, remote):
    from app.routes.accounts import accounts as accounts_bp

    _, state = remote
    add_account("c1")
    add_account("chk", type_="depository", subtype="checking")
    state["payload"] = {"liabilities": {"credit": [card("c1", [apr("purchase_apr", 24.99)])]}}
    refresh_item_liabilities("item-1", "tok", products={"liabilities"}, now=NOW)
    app_context.register_blueprint(accounts_bp, url_prefix="/api/accounts")
    rows = {
        r["account_id"]: r for r in app_context.test_client().get("/api/accounts/get_accounts").get_json()["accounts"]
    }
    c1, chk = rows["c1"], rows["chk"]
    assert c1["rate_status"] == "ok" and c1["rate_source"] == "plaid_liabilities"
    assert c1["minimum_payment_amount"] == 35.0 and c1["next_payment_due_date"] == "2026-11-01"
    assert c1["statement_balance"] == 410.25 and c1["interest_rate_breakdown"]["purchase_apr"]
    assert chk["rate_status"] is None and chk["minimum_payment_amount"] is None
    assert "access_token" not in json.dumps(c1)

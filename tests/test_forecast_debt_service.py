"""Debt settlement through the service and recurring API: confirmed plans, validation and warnings."""

import os
import sys
from datetime import timedelta
from decimal import Decimal

import pytest

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")

from app.extensions import db  # noqa: E402
from app.models import Account, RecurringStream  # noqa: E402
from app.routes.recurring import recurring  # noqa: E402
from app.services import recurring_repository as repo  # noqa: E402
from app.services.forecast_v2_service import compute_v2_forecast  # noqa: E402
from flask import Flask  # noqa: E402
from forecast_v2_world import START, seed_world  # noqa: E402

TODAY = START


@pytest.fixture()
def database(monkeypatch):
    app = Flask(__name__)
    app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", SQLALCHEMY_TRACK_MODIFICATIONS=False)
    db.init_app(app)
    app.register_blueprint(recurring, url_prefix="/api/recurring")
    monkeypatch.setenv(repo.OWNER_ENV, "alice")
    with app.app_context():
        db.create_all()
        seed_world()
        yield app
        db.session.remove()
        db.drop_all()


def compute(**overrides):
    payload = {"user_id": "alice", "start_date": START.isoformat(), "horizon_days": 60, **overrides}
    return compute_v2_forecast(payload, today=TODAY)


def add_payment(**overrides):
    fields = dict(
        account_id="chk",
        display_name="Card payment",
        amount_cash_delta="-500.00",
        cadence="monthly",
        anchor_date=START + timedelta(days=14),
        event_role="liability_payment",
        funding_account_id="chk",
        destination_account_id="card",
    )
    fields.update(overrides)
    return repo.create_manual("alice", **fields)


def test_without_a_payment_plan_the_response_reports_proxy_coverage_and_unchanged_cash(database):
    result = compute()
    coverage = result["metadata"]["debt_payment_coverage"]
    assert coverage["mode"] == "proxy" and coverage["included"] == []
    assert coverage["unknown_payment_account_ids"] == ["card"] and coverage["unmodeled_account_count"] == 1
    assert not [c for c in result["cashflows"] if c["category"] == "liability_payment"]


def test_a_confirmed_payment_plan_flows_into_the_forecast_with_provenance(database):
    baseline = compute()
    add_payment()
    result = compute()
    coverage = result["metadata"]["debt_payment_coverage"]
    assert coverage["mode"] == "settlement" and coverage["settled_account_ids"] == ["card"]
    assert [p["amount"] for p in coverage["included"]] == ["500.00", "500.00"]
    assert coverage["included"][0]["destination_account_id"] == "card"
    payments = [c for c in result["cashflows"] if c["category"] == "liability_payment"]
    assert len(payments) == 2
    assert payments[0]["metadata"]["destination_account_id"] == "card"
    assert payments[0]["metadata"]["funding_account_id"] == "chk"
    assert "access_token" not in str(result) and "secret" not in str(result).lower()
    # Cash falls by the payments, but the card purchases that used to be cash proxies are gone.
    assert result["summary"]["total_outflows"] != baseline["summary"]["total_outflows"]
    liabilities = result["net_worth"]["liabilities"]
    assert liabilities["ending"] != liabilities["starting"]


def test_a_payment_plan_whose_accounts_are_not_in_scope_warns_and_is_ignored(database):
    add_payment()
    result = compute(excluded_account_ids=["chk"])  # funding account left out
    codes = {w["code"] for w in result["data_quality"]["warnings"]}
    assert "payment_plan_out_of_scope" in codes
    coverage = result["metadata"]["debt_payment_coverage"]
    assert coverage["included"] == [] and len(coverage["invalid_payment_stream_ids"]) == 1


def test_only_confirmed_plans_count_and_other_owners_never_leak(database):
    plan = add_payment()
    repo.update_stream("alice", plan.id, status="ignored")
    assert compute()["metadata"]["debt_payment_coverage"]["included"] == []
    repo.update_stream("alice", plan.id, status="confirmed")
    assert len(compute()["metadata"]["debt_payment_coverage"]["included"]) == 2
    bob = repo.create_manual(
        "bob", account_id="bob-chk", display_name="Bob", amount_cash_delta="-9", cadence="monthly",
        anchor_date=START + timedelta(days=3),
    )  # fmt: skip
    assert bob.event_role == "ordinary_expense"
    assert len(compute()["metadata"]["debt_payment_coverage"]["included"]) == 2


# ----------------------------------------------------------------------------- validation + API


@pytest.mark.parametrize(
    "override, status",
    [
        ({"funding_account_id": "card"}, 400),  # funded from a liability
        ({"funding_account_id": "brk"}, 400),  # funded from a brokerage account
        ({"destination_account_id": "sav"}, 400),  # paying a deposit account
        ({"destination_account_id": "bob-chk"}, 404),  # someone else's account
        ({"funding_account_id": "bob-chk"}, 404),
        ({"funding_account_id": None}, 400),
        ({"destination_account_id": None}, 400),
        ({"funding_account_id": "chk", "destination_account_id": "chk"}, 400),
        ({"amount_cash_delta": "500.00"}, 400),  # a payment is cash leaving the account
        ({"event_role": "bogus"}, 400),
    ],
)
def test_invalid_payment_plans_are_rejected_without_writing(database, override, status):
    body = {
        "account_id": "chk",
        "display_name": "Card payment",
        "amount_cash_delta": "-500.00",
        "cadence": "monthly",
        "anchor_date": "2026-11-15",
        "event_role": "liability_payment",
        "funding_account_id": "chk",
        "destination_account_id": "card",
        **override,
    }
    response = database.test_client().post("/api/recurring/streams", json=body)
    assert response.status_code == status
    assert RecurringStream.query.count() == 0


def test_roles_only_apply_to_the_right_streams_and_update_revalidates(database):
    client = database.test_client()
    ok = client.post(
        "/api/recurring/streams",
        json={
            "account_id": "chk",
            "display_name": "Card payment",
            "amount_cash_delta": "-500.00",
            "cadence": "monthly",
            "anchor_date": "2026-11-15",
            "event_role": "liability_payment",
            "funding_account_id": "chk",
            "destination_account_id": "card",
        },
    )
    assert ok.status_code == 201
    stream = ok.get_json()["stream"]
    assert (stream["event_role"], stream["funding_account_id"], stream["destination_account_id"]) == (
        "liability_payment",
        "chk",
        "card",
    )
    sid = stream["stream_id"]
    assert client.patch(f"/api/recurring/streams/{sid}", json={"destination_account_id": "sav"}).status_code == 400
    assert client.patch(f"/api/recurring/streams/{sid}", json={"amount_cash_delta": "500"}).status_code == 400
    assert client.patch(f"/api/recurring/streams/{sid}", json={"amount_cash_delta": "-450.00"}).status_code == 200
    unchanged = repo.get_stream("alice", sid)
    assert unchanged.amount_cash_delta == Decimal("-450.00") and unchanged.destination_account_id == "card"

    ordinary = client.post(
        "/api/recurring/streams",
        json={
            "account_id": "chk",
            "display_name": "Rent",
            "amount_cash_delta": "-900.00",
            "cadence": "monthly",
            "anchor_date": "2026-11-01",
            "funding_account_id": "chk",
        },
    )
    assert ordinary.status_code == 400  # funding/destination only apply to payments and transfers
    income = client.post(
        "/api/recurring/streams",
        json={
            "account_id": "chk",
            "display_name": "Pay",
            "amount_cash_delta": "-10.00",
            "cadence": "monthly",
            "anchor_date": "2026-11-01",
            "event_role": "income",
        },
    )
    assert income.status_code == 400
    assert Account.query.filter_by(account_id="chk").one().user_id == "alice"

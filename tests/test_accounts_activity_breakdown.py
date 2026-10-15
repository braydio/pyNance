"""Tests for GET /api/accounts/activity_breakdown and the net_changes movement fields."""

import os
import sys
from datetime import date, timedelta
from decimal import Decimal

import pytest
from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)

os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")

from app.extensions import db  # noqa: E402
from app.models import Account, Transaction  # noqa: E402

D = Decimal


@pytest.fixture()
def client():
    from app.routes.accounts import accounts as accounts_bp

    app = Flask(__name__)
    app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", SQLALCHEMY_TRACK_MODIFICATIONS=False)
    db.init_app(app)
    app.register_blueprint(accounts_bp, url_prefix="/api/accounts")
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


_counter = {"n": 0}


def add_tx(account_id, amount, day, **kw):
    _counter["n"] += 1
    db.session.add(
        Transaction(
            transaction_id=f"t{_counter['n']}",
            account_id=account_id,
            amount=D(str(amount)),
            date=day,
            description="x",
            pending=kw.get("pending", False),
            is_internal=kw.get("is_internal", False),
        )
    )


def add_account(account_id, user_id="u1", hidden=False):
    db.session.add(
        Account(account_id=account_id, user_id=user_id, name=account_id, type="depository", is_hidden=hidden)
    )


def get(client, **params):
    return client.get("/api/accounts/activity_breakdown", query_string=params)


def rows(response):
    return {r["account_id"]: r for r in response.get_json()["accounts"]}


def test_counts_are_not_capped_at_100_and_use_absolute_value(client):
    add_account("a")
    for i in range(150):
        add_tx("a", 10 if i % 2 else -10, date(2026, 9, 15))
    db.session.commit()
    body = get(client, start_date="2026-09-01", end_date="2026-09-30")
    row = rows(body)["a"]
    assert row["transaction_count"] == 150
    assert row["transaction_value_abs"] == 1500.0
    assert body.get_json()["period"] == {"start_date": "2026-09-01", "end_date": "2026-09-30", "inclusive": True}


def test_date_bounds_are_inclusive_and_exclude_outside(client):
    add_account("a")
    add_tx("a", 5, date(2026, 8, 31))
    add_tx("a", 5, date(2026, 9, 1))
    add_tx("a", 5, date(2026, 9, 30))
    add_tx("a", 5, date(2026, 10, 1))
    db.session.commit()
    assert rows(get(client, start_date="2026-09-01", end_date="2026-09-30"))["a"]["transaction_count"] == 2


def test_pending_excluded_by_default_and_internal_transfers_reported_separately(client):
    add_account("a")
    add_tx("a", -20, date(2026, 9, 2), pending=True)
    add_tx("a", -30, date(2026, 9, 3), is_internal=True)
    add_tx("a", 40, date(2026, 9, 4))
    db.session.commit()
    body = get(client, start_date="2026-09-01", end_date="2026-09-30")
    row = rows(body)["a"]
    assert row["transaction_count"] == 2 and row["transaction_value_abs"] == 70.0
    assert row["internal_transfer_count"] == 1 and row["internal_transfer_value_abs"] == 30.0
    assert body.get_json()["treatment"]["pending"] == "excluded"
    with_pending = get(client, start_date="2026-09-01", end_date="2026-09-30", include_pending="true")
    assert rows(with_pending)["a"]["transaction_count"] == 3


def test_owner_isolation_and_no_enumeration(client):
    add_account("mine", user_id="u1")
    add_account("theirs", user_id="u2")
    add_tx("mine", 1, date(2026, 9, 2))
    add_tx("theirs", 1, date(2026, 9, 2))
    db.session.commit()
    scoped = rows(get(client, start_date="2026-09-01", end_date="2026-09-30", user_id="u1"))
    assert set(scoped) == {"mine"}
    asked = get(client, start_date="2026-09-01", end_date="2026-09-30", user_id="u1", account_ids="theirs,ghost")
    assert asked.status_code == 200 and asked.get_json()["accounts"] == []  # same as nonexistent


def test_hidden_accounts_require_opt_in(client):
    add_account("v")
    add_account("h", hidden=True)
    db.session.commit()
    params = {"start_date": "2026-09-01", "end_date": "2026-09-30"}
    assert set(rows(get(client, **params))) == {"v"}
    assert set(rows(get(client, include_hidden="true", **params))) == {"v", "h"}


def test_empty_range_returns_zero_rows_with_coverage(client):
    add_account("a")
    db.session.commit()
    body = get(client, start_date="2026-09-01", end_date="2026-09-30").get_json()
    assert body["accounts"][0]["transaction_count"] == 0
    assert body["coverage"] == {"accounts_considered": 1, "accounts_with_activity": 0, "include_hidden": False}


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"start_date": "2026-09-01"},
        {"start_date": "09/01/2026", "end_date": "2026-09-30"},
        {"start_date": "2026-9-1", "end_date": "2026-09-30"},
        {"start_date": "2026-13-01", "end_date": "2026-13-02"},
        {"start_date": "2026-09-30", "end_date": "2026-09-01"},
        {"start_date": "2000-01-01", "end_date": "2026-09-01"},
    ],
)
def test_invalid_dates_are_rejected(client, params):
    response = get(client, **params)
    assert response.status_code == 400 and response.get_json()["status"] == "error"


def test_net_changes_reports_movement_not_income_and_excludes_pending(client):
    add_account("a")
    today = date.today()
    add_tx("a", 100, today - timedelta(days=1))
    add_tx("a", -40, today - timedelta(days=1))
    add_tx("a", -500, today - timedelta(days=1), pending=True)
    db.session.commit()
    data = client.get(
        "/api/accounts/a/net_changes",
        query_string={"start_date": (today - timedelta(days=2)).isoformat(), "end_date": today.isoformat()},
    ).get_json()["data"]
    assert (data["money_in"], data["money_out"], data["net_movement"]) == (100.0, 40.0, 60.0)
    assert data["income"] == 100.0 and data["expense"] == 40.0  # legacy aliases
    assert data["transaction_count"] == 2 and data["pending_excluded"] is True
    assert "balance_change" in data

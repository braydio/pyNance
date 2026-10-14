"""DB adapter for Forecast V2 sources: ownership scoping and as-of isolation."""

import os

os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")

from datetime import date, timedelta
from decimal import Decimal

import pytest
from app.extensions import db
from app.models import Account, AccountHistory, RecurringTransaction, Transaction
from app.services.forecast_v2_sources import build_user_v2_inputs, load_v2_source_data
from flask import Flask
from forecast.v2_core import simulate_cash_ledger

AS_OF = date(2026, 10, 31)


@pytest.fixture()
def database():
    app = Flask(__name__)
    app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", SQLALCHEMY_TRACK_MODIFICATIONS=False)
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def add_account(account_id, user_id, acct_type="depository", subtype="checking", **extra):
    account = Account(account_id=account_id, user_id=user_id, name=account_id, type=acct_type, subtype=subtype, **extra)
    db.session.add(account)
    return account


def add_tx(transaction_id, account_id, day, amount, description, user_id="alice", **extra):
    transaction = Transaction(
        transaction_id=transaction_id,
        user_id=user_id,
        account_id=account_id,
        date=day,
        amount=Decimal(str(amount)),
        description=description,
        **extra,
    )
    db.session.add(transaction)
    return transaction


def seed():
    add_account("alice-chk", "alice")
    add_account("alice-hidden", "alice", is_hidden=True)
    add_account("bob-chk", "bob")
    db.session.flush()
    db.session.add_all(
        [
            AccountHistory(
                account_id="alice-chk", user_id="alice", date=AS_OF - timedelta(days=1), balance=Decimal("1000.00")
            ),
            AccountHistory(account_id="alice-chk", user_id="alice", date=AS_OF, balance=Decimal("1200.00")),
            AccountHistory(
                account_id="alice-chk", user_id="alice", date=AS_OF + timedelta(days=5), balance=Decimal("9999.00")
            ),
            AccountHistory(account_id="bob-chk", user_id="bob", date=AS_OF, balance=Decimal("777.00")),
        ]
    )
    for i in range(60):
        day = AS_OF - timedelta(days=i)
        add_tx(f"a-{i}", "alice-chk", day, -10 - i % 5, f"Store {i}")
    add_tx("a-future", "alice-chk", AS_OF + timedelta(days=3), -5000, "Future")
    add_tx("a-hidden", "alice-hidden", AS_OF, -123, "Hidden account")
    add_tx("b-1", "bob-chk", AS_OF, -999, "Bob only", user_id="bob")
    db.session.commit()


def test_loader_is_scoped_to_user_and_excludes_hidden_foreign_and_future_rows(database):
    seed()
    data = load_v2_source_data(user_id="alice", as_of_date=AS_OF)
    assert [a["account_id"] for a in data["accounts"]] == ["alice-chk"]
    ids = {t["transaction_id"] for t in data["transactions"]}
    assert "a-future" not in ids and "a-hidden" not in ids and "b-1" not in ids
    assert len(ids) == 60


def test_included_account_ids_can_only_narrow_never_widen(database):
    seed()
    data = load_v2_source_data(user_id="alice", as_of_date=AS_OF, included_account_ids=["bob-chk", "alice-chk"])
    assert [a["account_id"] for a in data["accounts"]] == ["alice-chk"]
    assert data["ignored_account_ids"] == ["bob-chk"]
    only_bob = load_v2_source_data(user_id="alice", as_of_date=AS_OF, included_account_ids=["bob-chk"])
    assert only_bob["accounts"] == [] and only_bob["transactions"] == []


def test_balance_snapshot_is_as_of_not_latest_and_missing_is_none(database):
    seed()
    data = load_v2_source_data(user_id="alice", as_of_date=AS_OF - timedelta(days=3))
    assert data["accounts"][0]["balance"] is None  # no snapshot on/before that date; never use today's
    on_date = load_v2_source_data(user_id="alice", as_of_date=AS_OF)
    assert on_date["accounts"][0]["balance"] == Decimal("1200.00")
    assert on_date["accounts"][0]["as_of"] == AS_OF


def test_user_id_is_required(database):
    with pytest.raises(ValueError):
        load_v2_source_data(user_id="", as_of_date=AS_OF)


def test_saved_recurring_rule_is_loaded_and_promoted_without_double_counting(database):
    add_account("alice-chk", "alice")
    db.session.flush()
    db.session.add(AccountHistory(account_id="alice-chk", user_id="alice", date=AS_OF, balance=Decimal("5000.00")))
    rent = [
        add_tx(f"rent-{m}", "alice-chk", date(2026, m, 1), -1850, "LANDLORD", merchant_slug="landlord")
        for m in (8, 9, 10)
    ]
    for i in range(40):
        add_tx(f"g-{i}", "alice-chk", AS_OF - timedelta(days=i), -15 - i % 4, f"Grocer {i}")
    db.session.flush()
    db.session.add(
        RecurringTransaction(
            transaction_id=rent[-1].transaction_id,
            account_id="alice-chk",
            frequency="monthly",
            next_due_date=date(2026, 11, 1),
        )
    )
    db.session.commit()

    result = build_user_v2_inputs(user_id="alice", as_of_date=AS_OF, horizon_days=45)
    bills = [e for e in result["scheduled_events"] if e.kind == "scheduled_bill"]
    assert [e.source for e in bills] == ["recurring", "recurring"]
    assert [e.date.isoformat() for e in bills] == ["2026-11-01", "2026-12-01"]
    assert not [s for s in result["streams"] if s["origin"] == "inferred" and s["merchant_key"] == "landlord"]
    buckets = {e["transaction_id"]: e["bucket"] for e in result["allocation_audit"]}
    assert {buckets[t.transaction_id] for t in rent} == {"scheduled"}

    ledger = simulate_cash_ledger(
        start_date=date(2026, 11, 1),
        horizon_days=45,
        account_snapshots=result["account_snapshots"],
        events=result["scheduled_events"] + result["residual_events"],
        owner_id="alice",
    )
    assert ledger.status == "ok" and ledger.daily[0].starting_cash == Decimal("5000.00")


def test_foreign_included_account_cannot_leak_into_a_forecast(database):
    seed()
    result = build_user_v2_inputs(user_id="alice", as_of_date=AS_OF, horizon_days=10, included_account_ids=["bob-chk"])
    assert result["allocation_audit"] == [] and result["account_snapshots"] == []
    assert result["ignored_account_ids"] == ["bob-chk"]

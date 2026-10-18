"""Cross-page financial truth gate (TP-20261016-011): one fixed world, no live Plaid calls.

The world is frozen at ``AS_OF`` and checks the corrected finance semantics end to end: signs,
card purchase plus settlement, recurring scans, Transfer Review scoping and hidden accounts.
"""

import os

os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")

from datetime import date, timedelta
from decimal import Decimal

import pytest
from app.extensions import db
from app.models import Account, RecurringStream, Transaction
from app.routes import recurring as recurring_routes
from app.routes.recurring import recurring
from app.routes.transactions import transactions
from app.services import recurring_repository as repo
from app.services.transaction_flow_classification import load_classified_flows, rollup_by_day
from app.services.transaction_semantics import canonical_account_delta
from flask import Flask

AS_OF = date(2026, 10, 16)
DAY = AS_OF - timedelta(days=2)


def _account(account_id, user, name, acct_type, subtype, **extra):
    return Account(
        account_id=account_id,
        user_id=user,
        name=name,
        institution_name="Bank",
        type=acct_type,
        subtype=subtype,
        **extra,
    )


def _tx(txid, account, raw, day=DAY, desc="Row", user="alice", provider="plaid", **extra):
    """Add a row; ``raw`` is the stored amount (Plaid: + outflow / - inflow)."""
    db.session.add(
        Transaction(
            transaction_id=txid,
            user_id=user,
            account_id=account,
            date=day,
            amount=Decimal(str(raw)),
            provider=provider,
            description=desc,
            **extra,
        )
    )


def seed_world():
    """Two checking, savings, credit card, IRA, 17 hidden accounts, a second owner."""
    db.session.add_all(
        [
            _account("chk1", "alice", "Checking 1", "depository", "checking"),
            _account("chk2", "alice", "Checking 2", "depository", "checking"),
            _account("sav", "alice", "Savings", "depository", "savings"),
            _account("card", "alice", "Card", "credit", "credit card"),
            _account("ira", "alice", "IRA", "investment", "ira"),
            _account("bob-chk", "bob", "Bob Checking", "depository", "checking"),
        ]
        + [_account(f"hid{i:02d}", "alice", f"Hidden {i}", "depository", "checking", is_hidden=True) for i in range(17)]
    )
    db.session.flush()
    _tx("payroll", "chk1", "-2000.00", desc="ACME PAYROLL", category_slug="INCOME_WAGES")
    _tx("card-buy", "card", "50.00", desc="Coffee Roasters")
    _tx("hidden-spend", "hid00", "999.00", desc="Hidden spend")
    for month in (7, 8, 9):  # three similar merchant charges, distinct amounts and merchants
        _tx(f"stream-a{month}", "chk1", "700.00", day=date(2026, month, 21), desc=f"RENT PAYMENT {month:02d}")
    _tx("xfer-out", "chk1", "200.00", day=AS_OF - timedelta(days=1), desc="Transfer to savings")
    _tx("xfer-in", "sav", "-200.00", day=AS_OF - timedelta(days=1), desc="Transfer from checking")
    _tx("bob-in", "bob-chk", "-200.00", day=AS_OF - timedelta(days=1), desc="Transfer", user="bob")
    db.session.commit()


@pytest.fixture()
def app(monkeypatch):
    flask_app = Flask(__name__)
    flask_app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", SQLALCHEMY_TRACK_MODIFICATIONS=False)
    db.init_app(flask_app)
    flask_app.register_blueprint(recurring, url_prefix="/api/recurring")
    flask_app.register_blueprint(transactions, url_prefix="/api/transactions")
    monkeypatch.setenv(repo.OWNER_ENV, "alice")

    class FrozenDate(date):
        @classmethod
        def today(cls):
            return AS_OF

    monkeypatch.setattr(recurring_routes, "date", FrozenDate)
    with flask_app.app_context():
        db.create_all()
        seed_world()
        yield flask_app
        db.session.remove()
        db.drop_all()


def test_plaid_signs_give_cash_effect_and_income_positive():
    assert canonical_account_delta(provider="plaid", raw_amount="50.00", account_type="depository") == Decimal("-50.00")
    assert canonical_account_delta(provider="plaid", raw_amount="-2000.00", account_type="depository") == Decimal(
        "2000.00"
    )


def test_card_purchase_is_one_expense_and_hidden_accounts_are_excluded(app):
    flows = load_classified_flows("alice", AS_OF - timedelta(days=30), AS_OF)
    ids = {f.tx.transaction_id for f in flows}
    assert "hidden-spend" not in ids and {"payroll", "card-buy"} <= ids
    day = rollup_by_day(flows)[DAY.isoformat()]
    assert day["income"] == Decimal("2000.00")
    assert day["expenses"] == Decimal("-50.00")  # charged once, never deducted again
    assert day["income"] + day["expenses"] == Decimal("1950.00")
    assert day["debt_settlement"] == Decimal("0.00")


def test_unlinked_transfer_rows_do_not_become_income(app):
    flows = load_classified_flows("alice", AS_OF - timedelta(days=30), AS_OF)
    income = sum((f.economic_amount for f in flows if f.economic_amount and f.economic_amount > 0), Decimal(0))
    assert income == Decimal("2000.00")  # the unconfirmed $200 savings leg never adds to income
    inflow = next(f for f in flows if f.tx.transaction_id == "xfer-in")
    assert inflow.flow_kind == "unclassified" and inflow.economic_amount is None


def test_recurring_scan_is_idempotent_ignores_stay_ignored_and_creates_no_transactions(app):
    client = app.test_client()
    before = Transaction.query.count()
    first = client.post("/api/recurring/scan/chk1").get_json()["scan"]
    assert first["created"] == 1
    stream = RecurringStream.query.one()
    assert stream.status == "proposed"  # never auto-confirmed
    client.post("/api/recurring/scan/chk1")
    assert RecurringStream.query.count() == 1

    repo.update_stream("alice", stream.id, status="ignored")
    client.post("/api/recurring/scan/chk1")
    assert db.session.get(RecurringStream, stream.id).status == "ignored"
    assert RecurringStream.query.count() == 1 and Transaction.query.count() == before


def test_transfer_scan_is_owner_scoped_read_only_and_fails_closed(app, monkeypatch):
    client = app.test_client()
    body = client.post("/api/transactions/scan-internal").get_json()
    assert len(body["pairs"]) == 1
    assert {body["pairs"][0]["left"]["transaction_id"], body["pairs"][0]["right"]["transaction_id"]} == {
        "xfer-out",
        "xfer-in",
    }
    assert "bob" not in str(body)
    assert {t.is_internal for t in Transaction.query.all()} <= {False, None}

    monkeypatch.delenv(repo.OWNER_ENV, raising=False)
    closed = client.post("/api/transactions/scan-internal")
    assert closed.status_code == 503 and "pairs" not in closed.get_json()

    monkeypatch.setenv(repo.OWNER_ENV, "bob")
    foreign = client.post("/api/recurring/scan/chk1")
    assert foreign.status_code == 404  # alice's account is invisible to another owner

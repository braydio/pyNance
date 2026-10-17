"""Safe-to-spend cash basis: deficits, availability, noncash exclusion, no double debit (synthetic)."""

import importlib
import os
import sys
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from flask import Flask

AS_OF = date(2026, 10, 17)
NOW = datetime.now(timezone.utc)  # freshness is judged against the wall clock


@pytest.fixture()
def env():
    os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
    saved = {k: v for k, v in sys.modules.items() if k == "app" or k.startswith("app.")}
    for key in saved:
        sys.modules.pop(key)
    try:
        db = importlib.import_module("app.extensions").db
        models = importlib.import_module("app.models")
        service = importlib.import_module("app.services.safe_to_spend")
        app = Flask(__name__)
        app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", SQLALCHEMY_TRACK_MODIFICATIONS=False)
        db.init_app(app)
        with app.app_context():
            db.create_all()
            yield db, models, service
            db.session.remove()
            db.drop_all()
    finally:
        for key in list(sys.modules):
            if key == "app" or key.startswith("app."):
                sys.modules.pop(key)
        sys.modules.update(saved)
        sys.path.pop(0)


def account(models, aid, balance, *, kind="depository", subtype="checking", owner="u", **extra):
    return models.Account(
        account_id=aid,
        user_id=owner,
        name=extra.pop("name", aid),
        type=kind,
        subtype=subtype,
        balance=Decimal(str(balance)),
        **extra,
    )


def payload(db, service, owner="u", **kw):
    db.session.commit()
    inputs = service.SafeToSpendInputs(user_id=owner, as_of=AS_OF, buffer_cents=0, **kw)
    return service.build_safe_to_spend_payload(inputs)


def tx(models, txid, aid, amount, **extra):
    return models.Transaction(
        transaction_id=txid,
        account_id=aid,
        user_id=None,
        provider="plaid",
        amount=Decimal(str(amount)),
        date=AS_OF,
        description="x",
        **extra,
    )


def test_overdraft_is_a_deficit_against_other_cash_not_added_back(env):
    db, models, service = env
    db.session.add_all([account(models, "chk", -100), account(models, "sav", 200, subtype="savings")])
    data = payload(db, service)
    assert data["components"]["spendable_cash_cents"] == 10_000  # at most $100, never $200 or $300
    assert data["cash_coverage"]["deficit_cents"] == 10_000 and data["cash_coverage"]["deficit_accounts"] == 1
    by_id = {a["account_id"]: a for a in data["accounts"]}
    assert by_id["chk"]["deficit_cents"] == 10_000 and by_id["chk"]["balance_cents"] == 0


def test_deficit_larger_than_cash_clamps_to_zero(env):
    db, models, service = env
    db.session.add_all([account(models, "chk", -500), account(models, "sav", 200, subtype="savings")])
    assert payload(db, service)["components"]["spendable_cash_cents"] == 0


def test_available_balance_caps_current_balance_and_missing_is_flagged(env):
    db, models, service = env
    db.session.add_all(
        [
            account(models, "held", 1000, available_balance=Decimal("700"), balance_as_of=NOW),
            account(models, "plain", 300, subtype="savings", balance_as_of=NOW),
        ]
    )
    data = payload(db, service)
    assert data["components"]["spendable_cash_cents"] == 100_000
    by_id = {a["account_id"]: a for a in data["accounts"]}
    assert by_id["held"]["balance_cents"] == 70_000 and by_id["held"]["warnings"] == []
    assert "availability_unverified" in by_id["plain"]["warnings"]
    assert data["cash_coverage"]["availability_unverified"] == 1
    assert data["confidence"] != "ready"


def test_stale_and_unknown_balance_age_lower_confidence_not_cash(env):
    db, models, service = env
    old = datetime(2026, 10, 1, tzinfo=timezone.utc)
    db.session.add_all(
        [
            account(models, "old", 100, available_balance=Decimal("100"), balance_as_of=old),
            account(models, "new", 50, subtype="savings", available_balance=Decimal("50")),
        ]
    )
    data = payload(db, service)
    assert data["components"]["spendable_cash_cents"] == 15_000
    assert data["cash_coverage"]["stale_balances"] == 1 and data["cash_coverage"]["unknown_freshness"] == 1


def test_name_never_qualifies_and_noncash_types_are_excluded(env):
    db, models, service = env
    db.session.add_all(
        [
            account(models, "cashback", 400, kind="credit", subtype="credit card", name="Cash Back Visa"),
            account(models, "brk", 900, kind="investment", subtype="brokerage", is_investment=True),
            account(models, "loan", 300, kind="loan", subtype="student"),
            account(models, "hid", 800, is_hidden=True),
            account(models, "cd", 600, subtype="cd"),
            account(models, "other", 700, owner="someone-else"),
            account(models, "chk", 25),
        ]
    )
    data = payload(db, service)
    assert data["components"]["spendable_cash_cents"] == 2_500
    assert [a["account_id"] for a in data["accounts"]] == ["chk"]


def test_posted_spending_is_shown_but_not_deducted_twice(env):
    db, models, service = env
    db.session.add_all(
        [
            account(models, "chk", 500, available_balance=Decimal("500")),
            account(models, "card", -90, kind="credit", subtype="credit card"),
        ]
    )
    db.session.add_all([tx(models, "posted", "chk", "50"), tx(models, "cardbuy", "card", "90")])
    data = payload(db, service)
    comps = data["components"]
    assert comps["spendable_cash_cents"] == 50_000 and data["total_horizon_cents"] == 50_000
    assert comps["spent_today_cents"] == 5_000  # the card purchase is not a cash outflow
    assert comps["spent_today_included_in_balance"] == "unknown"


def test_pending_cash_outflow_is_a_separate_unsubtracted_component(env):
    db, models, service = env
    db.session.add(account(models, "chk", 500, available_balance=Decimal("450")))
    db.session.add_all([tx(models, "pend", "chk", "40", pending=True), tx(models, "post", "chk", "10")])
    data = payload(db, service)
    comps = data["components"]
    assert comps["pending_cash_outflow_cents"] == 4_000 and comps["spent_today_cents"] == 1_000
    assert comps["spendable_cash_cents"] == 45_000  # the provider's available balance already carries the hold


def test_internal_transfers_are_not_cash_outflow_and_owners_are_isolated(env):
    db, models, service = env
    db.session.add_all([account(models, "mine", 100), account(models, "theirs", 999, owner="other")])
    db.session.add_all([tx(models, "t1", "mine", "30", is_internal=True), tx(models, "t2", "theirs", "70")])
    comps = payload(db, service)["components"]
    assert comps["spent_today_cents"] == 0 and comps["spendable_cash_cents"] == 10_000


def test_cents_are_stable_integers_for_fractional_balances(env):
    db, models, service = env
    db.session.add(account(models, "chk", "10.005", available_balance=Decimal("10.005")))
    value = payload(db, service)["components"]["spendable_cash_cents"]
    assert isinstance(value, int) and value == 1001

"""Sign contract for forecast inputs: Plaid provider sign, manual direction and reconciliation."""

import os

os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")

from datetime import date, timedelta
from decimal import Decimal

import pytest
from app.extensions import db
from app.models import Account, AccountHistory, Transaction
from app.routes.forecast import _load_historical_aggregates
from app.services.forecast_v2_sources import build_user_v2_inputs, load_v2_source_data
from app.services.transaction_semantics import (
    INVALID_AMOUNT,
    SIGN_UNKNOWN,
    canonical_account_delta,
    normalize_amount,
)
from flask import Flask

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


@pytest.mark.parametrize(
    "provider, raw, account_type, expected",
    [
        ("plaid", "60.00", "depository", Decimal("-60.00")),  # checking purchase -> cash out
        ("plaid", "-1000.00", "depository", Decimal("1000.00")),  # paycheck -> cash in
        ("plaid", "90.00", "credit", Decimal("-90.00")),  # card purchase -> debt up, no cash leaves
        ("plaid", "-90.00", "credit", Decimal("90.00")),  # card payment -> debt down
        ("plaid", "0", "depository", Decimal("0")),
        ("PLAID", Decimal("12.34"), None, Decimal("-12.34")),  # provider is case-insensitive, cents kept
    ],
)
def test_plaid_amount_is_negated_for_cash_and_liability(provider, raw, account_type, expected):
    delta = canonical_account_delta(provider=provider, raw_amount=raw, account_type=account_type)
    assert delta == expected and isinstance(delta, Decimal)


@pytest.mark.parametrize(
    "direction, raw, expected",
    [
        ("inflow", "50", Decimal("50")),
        ("income", "-50", Decimal("50")),
        ("outflow", "50", Decimal("-50")),
        ("expense", "-50", Decimal("-50")),
        ("signed", "-50", Decimal("-50")),  # already + inflow / - outflow
        ("signed", "50", Decimal("50")),
    ],
)
def test_manual_amount_uses_the_explicit_direction(direction, raw, expected):
    assert canonical_account_delta(provider="manual", raw_amount=raw, manual_direction=direction) == expected


def test_manual_without_direction_is_unknown_not_an_expense():
    result = normalize_amount(provider="manual", raw_amount="-25")
    assert result.delta is None and result.warning == SIGN_UNKNOWN
    assert normalize_amount(provider="manual", raw_amount="25", manual_direction="sideways").delta is None
    assert normalize_amount(provider="other", raw_amount="25").warning == SIGN_UNKNOWN


@pytest.mark.parametrize("bad", [None, "abc", "NaN", "Infinity", float("nan"), float("inf")])
def test_non_finite_or_malformed_amounts_are_rejected(bad):
    result = normalize_amount(provider="plaid", raw_amount=bad)
    assert result.delta is None and result.warning == INVALID_AMOUNT


def _account(account_id, acct_type="depository", subtype="checking", user_id="alice"):
    db.session.add(Account(account_id=account_id, user_id=user_id, name=account_id, type=acct_type, subtype=subtype))


def _tx(txid, account_id, day, amount, provider="plaid", user_id="alice", **extra):
    db.session.add(
        Transaction(
            transaction_id=txid,
            user_id=user_id,
            account_id=account_id,
            date=day,
            amount=Decimal(str(amount)),
            provider=provider,
            description=txid,
            **extra,
        )
    )


def test_loader_normalizes_plaid_rows_keeps_audit_fields_and_excludes_unknown_manual(database):
    _account("chk")
    _account("card", "credit", "credit card")
    db.session.flush()
    _tx("coffee", "chk", AS_OF, "60.00")
    _tx("pay", "chk", AS_OF, "-1000.00")
    _tx("charge", "card", AS_OF, "90.00")
    _tx("manual-unknown", "chk", AS_OF, "-40.00", provider="manual")
    db.session.commit()

    data = load_v2_source_data(user_id="alice", as_of_date=AS_OF)
    by_id = {t["transaction_id"]: t for t in data["transactions"]}
    assert by_id["coffee"]["amount"] == Decimal("-60.00") and by_id["coffee"]["raw_amount"] == Decimal("60.00")
    assert by_id["pay"]["amount"] == Decimal("1000.00")
    assert by_id["charge"]["amount"] == Decimal("-90.00")
    assert by_id["charge"]["account_bucket"] == "liability" and by_id["coffee"]["account_bucket"] == "cash"
    assert by_id["coffee"]["source_provider"] == "plaid"
    assert by_id["coffee"]["amount_semantics"] == "plaid_provider_sign"
    assert "manual-unknown" not in by_id
    assert data["sign_summary"] == {"normalized": 3, "excluded": 1, "by_reason": {SIGN_UNKNOWN: 1}}


def test_card_purchase_is_not_an_immediate_bank_withdrawal(database):
    _account("chk")
    _account("card", "credit", "credit card")
    db.session.flush()
    db.session.add(AccountHistory(account_id="chk", user_id="alice", date=AS_OF, balance=Decimal("5000.00")))
    for i in range(30):
        _tx(f"c-{i}", "card", AS_OF - timedelta(days=i), 40)
    db.session.commit()

    result = build_user_v2_inputs(user_id="alice", as_of_date=AS_OF, horizon_days=14)
    buckets = {e["bucket"] for e in result["allocation_audit"]}
    assert "income" not in buckets  # purchases (raw +) must never be read as inflow
    assert all(e.amount <= 0 for e in result["residual_events"])


def test_historical_aggregates_use_canonical_deltas_and_skip_pending_internal_unknown(database):
    _account("chk")
    _account("card", "credit", "credit card")
    _account("other", user_id="bob")
    db.session.flush()
    day = AS_OF - timedelta(days=1)
    _tx("buy", "chk", day, "60.00")
    _tx("paycheck", "chk", day, "-1000.00")
    _tx("card-buy", "card", day, "90.00")
    _tx("pending", "chk", day, "500.00", pending=True)
    _tx("xfer", "chk", day, "300.00", is_internal=True)
    _tx("manual", "chk", day, "-777.00", provider="manual")
    _tx("bob", "other", day, "-9999.00", user_id="bob")
    db.session.commit()

    rows = _load_historical_aggregates("alice", AS_OF)
    assert len(rows) == 1
    assert rows[0]["inflow"] == 1000.0  # only the paycheck
    assert rows[0]["outflow"] == 150.0  # 60 checking purchase + 90 card charge


def test_reconciliation_start_plus_signed_events_equals_end(database):
    _account("chk")
    db.session.flush()
    start = Decimal("2000.00")
    rows = [("a", "60.00"), ("b", "-1000.00"), ("c", "12.34")]
    for i, (txid, raw) in enumerate(rows):
        _tx(txid, "chk", AS_OF - timedelta(days=i), raw)
    db.session.commit()

    data = load_v2_source_data(user_id="alice", as_of_date=AS_OF)
    net = sum((t["amount"] for t in data["transactions"]), Decimal("0.00"))
    assert net == Decimal("927.66")  # -60 + 1000 - 12.34
    assert start + net == Decimal("2927.66")

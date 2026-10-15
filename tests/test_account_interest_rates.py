"""Tests for observed interest charges and guarded effective-rate estimation."""

import os
import sys
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from flask import Flask

BASE_BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)

os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")

from app.extensions import db  # noqa: E402
from app.models import Account, Transaction  # noqa: E402
from app.services.account_interest_rates import (  # noqa: E402
    StatementCycle,
    apply_apr,
    can_overwrite_apr,
    estimate_effective_rate,
    interest_paid_between,
    is_contractual_apr,
    is_qualifying_interest_charge,
    qualifying_interest_charges,
    recent_interest_by_account,
)

D = Decimal


def tx(**overrides):
    base = {
        "transaction_id": "t1",
        "account_id": "a1",
        "amount": 20,
        "date": "2026-09-01",
        "name": "INTEREST CHARGE",
        "pending": False,
        "personal_finance_category": None,
        "category": None,
    }
    base.update(overrides)
    return base


def cycle(start, end, interest, adb, **kw):
    return StatementCycle(
        date.fromisoformat(start),
        date.fromisoformat(end),
        D(interest),
        D(adb) if adb else None,
        **{"balance_source": "statement", **kw},
    )


# --- classification ---------------------------------------------------------


def test_qualifies_by_pfc_exact_description_and_legacy_category():
    assert is_qualifying_interest_charge(
        tx(name="Anything", personal_finance_category={"detailed": "BANK_FEES_INTEREST_CHARGE"})
    )
    assert is_qualifying_interest_charge(tx(name="  Purchase  Interest Charge "))
    assert is_qualifying_interest_charge(tx(name="Whatever", category=["Bank Fees", "Interest Charge"]))


def test_excludes_pending_credits_reversals_and_generic_fees():
    assert not is_qualifying_interest_charge(tx(pending=True))
    assert not is_qualifying_interest_charge(tx(amount=-20))  # interest credit / reversal
    assert not is_qualifying_interest_charge(tx(name="Interest Earned"))
    assert not is_qualifying_interest_charge(tx(name="Savings Interest Payment"))
    assert not is_qualifying_interest_charge(
        tx(name="Late fee", personal_finance_category={"detailed": "BANK_FEES_LATE_PAYMENT"})
    )
    assert not is_qualifying_interest_charge(tx(name="Transfer to Interest Bearing Account"))
    assert not is_qualifying_interest_charge(tx(amount=0))


def test_duplicated_events_count_once_and_period_totals_are_exact():
    charges = [
        tx(transaction_id="t1", date="2026-08-31", amount=10),  # outside period
        tx(transaction_id="t2", date="2026-09-01", amount=20),
        tx(transaction_id="t3", date="2026-09-01", amount=20),  # duplicate delivery
        tx(transaction_id="t4", date="2026-09-30", amount=5),
    ]
    assert len(qualifying_interest_charges(charges)) == 3
    assert interest_paid_between(charges, date(2026, 9, 1), date(2026, 9, 30)) == D("25")


def test_transfers_are_not_interest():
    assert not is_qualifying_interest_charge(tx(name="Payment Thank You", category=["Transfer", "Credit Card"]))


# --- estimator -------------------------------------------------------------


def test_single_cycle_or_charge_gives_no_estimate():
    assert estimate_effective_rate([])["reason"] == "insufficient_cycles"
    result = estimate_effective_rate([cycle("2026-08-01", "2026-08-30", "20", "1000")])
    assert result["estimated_rate"] is None and result["reason"] == "insufficient_cycles"


def test_two_verified_30_day_cycles_produce_a_labelled_estimate():
    # 20 / 1000 over 30 days -> 100 * 0.02 * 365/30 = 24.33
    result = estimate_effective_rate(
        [cycle("2026-07-01", "2026-07-30", "20", "1000"), cycle("2026-07-31", "2026-08-29", "20", "1000")]
    )
    assert result["estimated_rate"] == pytest.approx(24.33, abs=0.01)
    assert result["confidence"] == "medium" and result["sample_cycles"] == 2
    assert result["kind"] == "effective_annualized_charge_rate"


def test_varying_cycle_lengths_are_annualized_per_day():
    result = estimate_effective_rate(
        [cycle("2026-01-01", "2026-01-31", "20", "1000"), cycle("2026-02-01", "2026-02-28", "18.08", "1000")]
    )
    assert result["estimated_rate"] == pytest.approx(23.5, abs=0.2)


@pytest.mark.parametrize("adb", [None, 0])
def test_zero_or_unknown_denominator(adb):
    result = estimate_effective_rate(
        [cycle("2026-07-01", "2026-07-30", "20", adb), cycle("2026-07-31", "2026-08-29", "20", "1000")]
    )
    assert result["estimated_rate"] is None and result["reason"] == "no_interest_bearing_balance"


def test_reconstructed_balances_are_not_verified():
    result = estimate_effective_rate(
        [
            cycle("2026-07-01", "2026-07-30", "20", "1000", balance_source="reconstructed"),
            cycle("2026-07-31", "2026-08-29", "20", "1000", balance_source="reconstructed"),
        ]
    )
    assert result["estimated_rate"] is None and result["reason"] == "unverified_balance"


def test_mixed_apr_buckets_and_dispersion_and_gaps_return_null():
    mixed = estimate_effective_rate(
        [
            cycle("2026-07-01", "2026-07-30", "20", "1000", mixed_apr=True),
            cycle("2026-07-31", "2026-08-29", "20", "1000"),
        ]
    )
    assert mixed["reason"] == "mixed_apr_buckets"
    wide = estimate_effective_rate(
        [cycle("2026-07-01", "2026-07-30", "10", "1000"), cycle("2026-07-31", "2026-08-29", "30", "1000")]
    )
    assert wide["reason"] == "high_dispersion"
    gap = estimate_effective_rate(
        [cycle("2026-05-01", "2026-05-30", "20", "1000"), cycle("2026-07-31", "2026-08-29", "20", "1000")]
    )
    assert gap["reason"] == "cycles_not_contiguous"


def test_no_interest_observed_is_not_zero_percent():
    result = estimate_effective_rate(
        [cycle("2026-07-01", "2026-07-30", "0", "1000"), cycle("2026-07-31", "2026-08-29", "0", "1000")]
    )
    assert result["estimated_rate"] is None and result["reason"] == "no_interest_observed"


# --- provenance ------------------------------------------------------------


def test_provider_precedence_and_legacy_unverified():
    assert can_overwrite_apr(None, "estimated")
    assert can_overwrite_apr("legacy_unverified", "estimated")
    assert not can_overwrite_apr("provider", "estimated")
    assert not can_overwrite_apr("manual", "estimated")
    assert can_overwrite_apr("manual", "provider")

    account = SimpleNamespace(apr=D("22.99"), apr_source="provider")
    assert apply_apr(account, 30, "estimated") is False and account.apr == D("22.99")
    assert is_contractual_apr(account)
    legacy = SimpleNamespace(apr=D("24.49"), apr_source="legacy_unverified")
    assert not is_contractual_apr(legacy)


def test_apr_is_percentage_units():
    account = SimpleNamespace(apr=None, apr_source=None)
    with pytest.raises(ValueError):
        apply_apr(account, 250, "manual")
    assert apply_apr(account, "23.49", "manual") and account.apr == D("23.49")


# --- persistence + API -----------------------------------------------------


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


def _seed():
    card = Account(
        account_id="card", name="Card", type="credit", subtype="credit card", balance=D("500"), apr=D("24.49")
    )
    loan = Account(account_id="loan", name="Loan", type="loan", balance=D("9000"))
    db.session.add_all([card, loan])
    db.session.commit()
    today = date.today()
    for idx, (acct, name, amount, pending) in enumerate(
        [
            ("card", "INTEREST CHARGE", 20, False),
            ("card", "INTEREST CHARGE", 99, True),
            ("card", "Interest Refund", -5, False),
            ("loan", "INTEREST CHARGE", 40, False),
        ]
    ):
        db.session.add(
            Transaction(
                transaction_id=f"x{idx}",
                account_id=acct,
                amount=D(amount),
                date=today,
                description=name,
                pending=pending,
            )
        )
    db.session.commit()


def test_recent_interest_only_for_cards_and_ignores_pending(app_context):
    _seed()
    accounts = Account.query.all()
    result = recent_interest_by_account(accounts)
    assert set(result) == {"card"}
    assert result["card"]["total"] == 20.0 and result["card"]["charge_count"] == 1
    assert result["card"]["source"] == "transactions"


def test_list_accounts_exposes_provenance_and_observed_interest(app_context):
    from app.routes.accounts import accounts as accounts_bp

    _seed()
    app_context.register_blueprint(accounts_bp, url_prefix="/api/accounts")
    rows = {
        r["account_id"]: r for r in app_context.test_client().get("/api/accounts/get_accounts").get_json()["accounts"]
    }
    card, loan = rows["card"], rows["loan"]
    assert card["apr"] == 24.49 and card["apr_source"] is None  # not claimed as provider data
    assert card["estimated_rate"] is None  # no verified ADB source yet
    assert card["interest_paid_recent"]["total"] == 20.0
    assert loan["interest_paid_recent"] is None and loan["estimated_rate"] is None

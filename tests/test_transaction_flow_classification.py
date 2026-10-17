"""Economic-flow classification: income vs spending vs movement, with the packet's fixtures."""

import os
import sys
from decimal import Decimal
from types import SimpleNamespace

import pytest

BASE_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)
os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")

from app.services.transaction_flow_classification import (  # noqa: E402
    LinkedPair,
    classify_reporting_flow,
    user_decision_for,
)

CHECKING = SimpleNamespace(
    account_id="chk", user_id="alice", type="depository", subtype="checking", is_investment=False
)
SAVINGS = SimpleNamespace(account_id="sav", user_id="alice", type="depository", subtype="savings", is_investment=False)
CARD = SimpleNamespace(account_id="card", user_id="alice", type="credit", subtype="credit card", is_investment=False)
BROKERAGE = SimpleNamespace(
    account_id="brk", user_id="alice", type="investment", subtype="brokerage", is_investment=True
)
FOREIGN = SimpleNamespace(account_id="bob", user_id="bob", type="depository", subtype="checking", is_investment=False)


def tx(txid, account, raw, pfc=None, **extra):
    """A Plaid-signed row: ``raw`` > 0 is money out, ``raw`` < 0 is money in."""
    base = dict(
        transaction_id=txid,
        account_id=account.account_id,
        provider="plaid",
        amount=Decimal(str(raw)),
        is_internal=False,
        internal_match_id=None,
        personal_finance_category=pfc,
        category_slug=None,
        description="",
        merchant_name=None,
        user_modified_fields=None,
    )
    base.update(extra)
    return SimpleNamespace(**base)


def pfc(primary, detailed=None):
    return {"primary": primary, "detailed": detailed or primary}


def kind(row, account, **kwargs):
    return classify_reporting_flow(row, account, **kwargs)["flow_kind"]


# ----------------------------------------------------------------------------- the packet fixtures


def test_a_verified_own_transfer_is_not_income_or_spending_on_either_side():
    inbound = tx(
        "in",
        CHECKING,
        -200,
        pfc("TRANSFER_IN", "TRANSFER_IN_ACCOUNT_TRANSFER"),
        is_internal=True,
        internal_match_id="out",
    )
    outbound = tx(
        "out",
        SAVINGS,
        200,
        pfc("TRANSFER_OUT", "TRANSFER_OUT_ACCOUNT_TRANSFER"),
        is_internal=True,
        internal_match_id="in",
    )
    a = classify_reporting_flow(inbound, CHECKING, linked_pair=LinkedPair(outbound, SAVINGS))
    b = classify_reporting_flow(outbound, SAVINGS, linked_pair=LinkedPair(inbound, CHECKING))
    assert (a["flow_kind"], b["flow_kind"]) == ("transfer", "transfer")
    assert a["economic_amount"] is None and b["economic_amount"] is None
    assert a["signed_account_delta"] == Decimal("200.00") and b["signed_account_delta"] == Decimal("-200.00")


def test_an_unpaired_brokerage_style_credit_is_review_not_income_and_nothing_is_marked():
    row = tx(
        "mystery",
        CHECKING,
        -100,
        pfc("TRANSFER_IN", "TRANSFER_IN_ACCOUNT_TRANSFER"),
        description="MSPBNA BANK TRANSFER",
    )
    result = classify_reporting_flow(row, CHECKING)
    assert result["flow_kind"] == "unclassified" and result["economic_amount"] is None
    assert result["reason_codes"] == ["pfc_account_transfer_unpaired"] and result["confidence"] == "low"
    assert row.is_internal is False and row.internal_match_id is None  # never auto-flagged

    counterpart = tx("cp", SAVINGS, 100, is_internal=True)  # does not point back yet
    paired = tx("mystery", CHECKING, -100, pfc("TRANSFER_IN"), is_internal=False, internal_match_id="cp")
    verified = classify_reporting_flow(paired, CHECKING, linked_pair=LinkedPair(counterpart, SAVINGS))
    assert verified["flow_kind"] == "unclassified"  # one-sided link: the counterpart does not point back
    counterpart.internal_match_id = "mystery"
    assert (
        classify_reporting_flow(paired, CHECKING, linked_pair=LinkedPair(counterpart, SAVINGS))["flow_kind"]
        == "transfer"
    )


def test_zelle_or_ach_wording_alone_is_never_proof_of_an_own_transfer():
    row = tx("z", CHECKING, -200, None, description="Zelle payment from Someone")
    assert kind(row, CHECKING) == "unclassified"
    assert classify_reporting_flow(row, CHECKING)["reason_codes"] == ["credit_without_evidence"]


@pytest.mark.parametrize(
    "row, account, expected, economic",
    [
        (tx("pay", CHECKING, -1000, pfc("INCOME", "INCOME_WAGES")), CHECKING, "income", Decimal("1000.00")),
        (tx("int", SAVINGS, -3, pfc("INCOME", "INCOME_INTEREST_EARNED")), SAVINGS, "income", Decimal("3.00")),
        (tx("ref", CHECKING, -25, pfc("GENERAL_MERCHANDISE")), CHECKING, "refund", Decimal("25.00")),
        (tx("ref2", CARD, -30, pfc("FOOD_AND_DRINK"), description="Refund Cafe"), CARD, "refund", Decimal("30.00")),
        (tx("buy", CARD, 42.5, pfc("GENERAL_MERCHANDISE")), CARD, "expense", Decimal("-42.50")),
        (tx("rent", CHECKING, 900, pfc("RENT_AND_UTILITIES")), CHECKING, "expense", Decimal("-900.00")),
        (tx("apr", CARD, 15, pfc("BANK_FEES", "BANK_FEES_INTEREST_CHARGE")), CARD, "expense", Decimal("-15.00")),
        (
            tx("fee", CHECKING, 12, pfc("BANK_FEES", "BANK_FEES_OTHER_BANK_FEES")),
            CHECKING,
            "expense",
            Decimal("-12.00"),
        ),
        (
            tx("loan", CHECKING, 220, pfc("LOAN_PAYMENTS", "LOAN_PAYMENTS_PERSONAL_LOAN_PAYMENT")),
            CHECKING,
            "debt_settlement",
            None,
        ),
        (
            tx("cardpay", CHECKING, 300, pfc("LOAN_PAYMENTS", "LOAN_PAYMENTS_CREDIT_CARD_PAYMENT")),
            CHECKING,
            "debt_settlement",
            None,
        ),
        (
            tx("cardrecv", CARD, -300, pfc("LOAN_PAYMENTS", "LOAN_PAYMENTS_CREDIT_CARD_PAYMENT")),
            CARD,
            "debt_settlement",
            None,
        ),
        (tx("deposit", CHECKING, -40, None), CHECKING, "unclassified", None),
        (tx("atm", CHECKING, 60, None), CHECKING, "expense", Decimal("-60.00")),
        (
            tx("contrib", CHECKING, 500, pfc("TRANSFER_OUT", "TRANSFER_OUT_INVESTMENT_AND_RETIREMENT_FUNDS")),
            CHECKING,
            "investment_movement",
            None,
        ),
        (
            tx("buyshares", BROKERAGE, 500, pfc("TRANSFER_OUT", "TRANSFER_OUT_INVESTMENT_AND_RETIREMENT_FUNDS")),
            BROKERAGE,
            "investment_movement",
            None,
        ),
        (tx("div", BROKERAGE, -9, pfc("INCOME", "INCOME_DIVIDENDS")), BROKERAGE, "income", Decimal("9.00")),
        (
            tx("proceeds", CHECKING, -500, pfc("TRANSFER_IN", "TRANSFER_IN_CASH_ADVANCES_AND_LOANS")),
            CHECKING,
            "unclassified",
            None,
        ),
        (tx("outflow", CHECKING, 5000, pfc("TRANSFER_OUT", "TRANSFER_OUT_SAVINGS")), CHECKING, "unclassified", None),
    ],
)
def test_classification_rules(row, account, expected, economic):
    result = classify_reporting_flow(row, account)
    assert result["flow_kind"] == expected
    assert result["economic_amount"] == economic
    assert result["signed_account_delta"] == -Decimal(str(row.amount)).quantize(Decimal("0.01"))  # bank movement kept


def test_a_user_rejecting_the_transfer_flag_is_trusted_over_provider_evidence():
    row = tx(
        "u",
        CHECKING,
        -75,
        pfc("TRANSFER_IN", "TRANSFER_IN_ACCOUNT_TRANSFER"),
        user_modified_fields='{"is_internal": true}',
    )
    assert user_decision_for(row) == "not_transfer"
    result = classify_reporting_flow(row, CHECKING, user_decision=user_decision_for(row))
    assert (result["flow_kind"], result["reason_codes"]) == ("income", ["user_not_transfer"])
    assert (
        user_decision_for(tx("v", CHECKING, 1, is_internal=True, user_modified_fields='{"is_internal": true}')) is None
    )
    assert user_decision_for(tx("w", CHECKING, 1, user_modified_fields="not json")) is None


@pytest.mark.parametrize(
    "mutation",
    [
        {"internal_match_id": "other"},  # does not point at this transaction
        {"account": FOREIGN},  # counterpart belongs to someone else
        {"account_id": "chk"},  # same account
        {"amount": Decimal("5.00")},  # not offsetting
    ],
)
def test_a_pair_is_verified_before_it_proves_a_transfer(mutation):
    row = tx("a", CHECKING, -200, pfc("TRANSFER_IN"), internal_match_id="b")
    other = tx("b", SAVINGS, 200, internal_match_id="a")
    other_account = mutation.pop("account", SAVINGS)
    for key, value in mutation.items():
        setattr(other, key, value)
    assert kind(row, CHECKING, linked_pair=LinkedPair(other, other_account)) == "unclassified"


def test_unknown_amount_direction_is_never_classified_as_money():
    manual = tx("m", CHECKING, -10, provider="manual")
    result = classify_reporting_flow(manual, CHECKING)
    assert result["flow_kind"] == "unclassified" and result["signed_account_delta"] is None
    assert result["economic_amount"] is None and result["reason_codes"] == ["sign_unknown"]
    assert kind(tx("bad", CHECKING, "NaN"), CHECKING) == "unclassified"


def test_classification_is_deterministic_and_never_mutates_the_row():
    row = tx("d", CHECKING, 33, pfc("FOOD_AND_DRINK"))
    snapshot = dict(vars(row))
    results = [classify_reporting_flow(row, CHECKING) for _ in range(3)]
    assert results[0] == results[1] == results[2]
    assert vars(row) == snapshot


def test_the_two_screenshot_credits_do_not_add_up_to_300_of_income():
    confirmed = tx(
        "z200",
        CHECKING,
        -200,
        pfc("TRANSFER_IN", "TRANSFER_IN_ACCOUNT_TRANSFER"),
        is_internal=True,
        internal_match_id="x",
    )
    candidate = tx(
        "b100", CHECKING, -100, pfc("TRANSFER_IN", "TRANSFER_IN_ACCOUNT_TRANSFER"), description="BANK TRANSFER"
    )
    income = sum(
        (r["economic_amount"] or Decimal(0))
        for r in (classify_reporting_flow(t, CHECKING) for t in (confirmed, candidate))
    )
    assert income == 0

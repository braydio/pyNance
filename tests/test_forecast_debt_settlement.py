"""Settlement-aware debt cash flows: payments move cash once, purchases raise the amount owed."""

import os
import sys
from datetime import date, timedelta
from decimal import Decimal

import pytest

BASE_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)
os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")

from forecast.v2_core import simulate_cash_ledger  # noqa: E402
from forecast.v2_sources import build_v2_inputs  # noqa: E402

AS_OF = date(2026, 10, 31)
START = date(2026, 11, 1)
HORIZON = 60

ACCOUNTS = [
    {"account_id": "chk", "type": "depository", "subtype": "checking", "balance": 4000},
    {"account_id": "sav", "type": "depository", "subtype": "savings", "balance": 1000},
    {
        "account_id": "card",
        "type": "credit",
        "subtype": "credit card",
        "balance": 12000,
        # Payment metadata exists but must never be turned into a payment on its own.
        "minimum_payment_amount": 250,
        "next_payment_due_date": "2026-11-20",
    },
    {"account_id": "loan", "type": "loan", "subtype": "student", "balance": 8000},
]

_n = {"v": 0}


def tx(day, amount, name, account="chk", **extra):
    _n["v"] += 1
    return {
        "transaction_id": f"d{_n['v']:05d}",
        "account_id": account,
        "date": day.isoformat(),
        "amount": amount,
        "name": name,
        **extra,
    }


def weekly_card_spend(amount=-100, days=120):
    """Irregular card purchases (no fixed cadence, distinct merchants) averaging about $100 a week."""
    out = []
    for offset in range(days):
        day = AS_OF - timedelta(days=offset)
        if offset % 4 == 0:
            out.append(tx(day, amount - (offset % 5) * 3, f"Mart {offset}", account="card"))
    return out


def chk_noise(days=120):
    return [tx(AS_OF - timedelta(days=o), -12, f"Coffee {o}") for o in range(0, days, 5)]


def payment_rule(**over):
    rule = {
        "rule_id": "stream:pay",
        "account_id": "chk",
        "amount": -500,
        "cadence": "monthly",
        "anchor_date": "2026-11-15",
        "event_role": "liability_payment",
        "funding_account_id": "chk",
        "destination_account_id": "card",
        "label": "Card payment",
    }
    rule.update(over)
    return rule


def build(transactions, rules=(), accounts=ACCOUNTS, **kwargs):
    return build_v2_inputs(
        transactions=transactions,
        recurring_rules=list(rules),
        accounts=accounts,
        as_of_date=AS_OF,
        start_date=START,
        horizon_days=HORIZON,
        **kwargs,
    )


def simulate(inputs, accounts=ACCOUNTS):
    snapshots = [{**a, "as_of": AS_OF.isoformat()} for a in accounts]
    return simulate_cash_ledger(
        start_date=START,
        horizon_days=HORIZON,
        account_snapshots=snapshots,
        events=inputs["scheduled_events"] + inputs["residual_events"],
        owner_id=None,
    )


def net_worth_gap(result):
    """Ending net worth minus starting net worth."""
    return result.daily[-1].net_worth - result.daily[0].net_worth


# ----------------------------------------------------------------------------- the contract


def test_a_large_balance_alone_never_reduces_cash():
    inputs = build(chk_noise())
    result = simulate(inputs)
    cov = inputs["debt_payment_coverage"]
    assert cov["included"] == [] and cov["mode"] == "proxy"
    assert cov["unmodeled_account_count"] == 2 and set(cov["unknown_payment_account_ids"]) == {"card", "loan"}
    # No $12k (or $250 minimum) leaves cash: the only outflow is the small checking noise.
    assert result.summary["total_outflows"] > -600
    assert result.daily[-1].liability_balance == Decimal("20000.00")  # owed amount untouched


def test_a_verified_payment_subtracts_exactly_its_amount_on_the_due_date():
    inputs = build(chk_noise(), rules=[payment_rule()])
    cov = inputs["debt_payment_coverage"]
    assert [
        (p["date"], p["amount"], p["funding_account_id"], p["destination_account_id"]) for p in cov["included"]
    ] == [
        ("2026-11-15", "500.00", "chk", "card"),
        ("2026-12-15", "500.00", "chk", "card"),
    ]
    baseline = simulate(build(chk_noise()))
    paid = simulate(inputs)
    by_day = {p.date.isoformat(): p for p in paid.daily}
    base_day = {p.date.isoformat(): p for p in baseline.daily}
    assert by_day["2026-11-15"].ending_cash - base_day["2026-11-15"].ending_cash == Decimal("-500.00")
    assert by_day["2026-11-14"].ending_cash == base_day["2026-11-14"].ending_cash
    assert paid.daily[-1].ending_cash - baseline.daily[-1].ending_cash == Decimal("-1000.00")


def test_a_payment_moves_cash_and_debt_together_so_net_worth_is_conserved():
    baseline = simulate(build(chk_noise()))
    paid = simulate(build(chk_noise(), rules=[payment_rule()]))
    assert paid.daily[-1].liability_balance == Decimal("19000.00")  # $12k card - $1k, $8k loan untouched
    assert net_worth_gap(paid) == net_worth_gap(baseline)  # paying debt is not spending


def test_purchases_on_a_settled_card_are_not_also_cash_spending():
    history = weekly_card_spend() + chk_noise()
    proxy = build(history)
    settled = build(history, rules=[payment_rule(amount=-400)])
    assert settled["debt_payment_coverage"]["mode"] == "mixed"  # the loan has no schedule

    audit = {e["transaction_id"]: e["bucket"] for e in settled["allocation_audit"]}
    card_rows = [t["transaction_id"] for t in history if t["account_id"] == "card"]
    assert {audit[i] for i in card_rows} == {"liability_charge"}
    proxy_audit = {e["transaction_id"]: e["bucket"] for e in proxy["allocation_audit"]}
    assert {proxy_audit[i] for i in card_rows} == {"residual"}

    # Proxy: the purchases are cash spending. Settlement: not one card row feeds the cash residual,
    # which is built from checking activity alone.
    residual_accounts = {e["account_id"] for e in settled["allocation_audit"] if e["bucket"] == "residual"}
    assert residual_accounts == {"chk"}
    assert "card" in {e["account_id"] for e in proxy["allocation_audit"] if e["bucket"] == "residual"}
    assert sum(e.amount for e in proxy["residual_events"] if e.kind == "residual") < sum(
        e.amount for e in settled["residual_events"] if e.kind == "residual"
    )
    charges = [e for e in settled["residual_events"] if e.kind == "liability_charge"]
    assert charges and all(e.account_id == "card" and e.amount > 0 for e in charges)


def test_reconciliation_card_purchase_payment_interest_and_a_savings_transfer_count_once():
    """$100 card purchase, $100 payment, $8 interest and a $50 checking->savings move."""
    card_history = weekly_card_spend(amount=-100) + [
        tx(AS_OF - timedelta(days=30 * k + 3), -8, "INTEREST CHARGE", account="card") for k in range(4)
    ]
    transfer_out = tx(AS_OF - timedelta(days=9), 50, "Transfer to savings", is_internal=True, internal_match_id="sv")
    transfer_in = {
        **tx(AS_OF - timedelta(days=9), -50, "Transfer from checking", account="sav", is_internal=True),
        "transaction_id": "sv",
    }
    transfer_out["amount"], transfer_in["amount"] = -50, 50
    history = card_history + chk_noise() + [transfer_out, transfer_in]

    inputs = build(history, rules=[payment_rule(amount=-100, cadence="weekly", anchor_date="2026-11-02")])
    audit = {e["transaction_id"]: e for e in inputs["allocation_audit"]}
    assert audit[transfer_out["transaction_id"]]["bucket"] == "transfer"  # consolidated cash moves nowhere
    assert audit["sv"]["bucket"] == "transfer"
    purchases = [e for e in inputs["allocation_audit"] if e["bucket"] == "liability_charge"]
    assert len(purchases) == len(weekly_card_spend(amount=-100))  # purchases raise the balance owed, not cash
    # The four monthly $8 interest charges are one recurring charge on the card (owed goes up, cash does not).
    assert {
        audit[i]["bucket"] for i in [t["transaction_id"] for t in card_history if t["name"] == "INTEREST CHARGE"]
    } == {"scheduled"}
    interest_events = [
        e for e in inputs["scheduled_events"] if e.kind == "liability_charge" and e.amount == Decimal("8.00")
    ]
    assert interest_events and all(e.account_id == "card" for e in interest_events)

    result = simulate(inputs)
    paid = sum(Decimal(p["amount"]) for p in inputs["debt_payment_coverage"]["included"])
    cash_down = result.daily[0].starting_cash - result.daily[-1].ending_cash
    noise = sum((e.amount for e in inputs["residual_events"] if e.kind == "residual" and e.amount < 0), Decimal("0"))
    # Cash fell by the payments plus ordinary checking spending, and by nothing for the card purchases.
    assert cash_down >= paid and cash_down + noise <= paid
    opening_owed = Decimal("20000.00")  # $12,000 card + $8,000 loan
    charged = sum(
        (e.amount for e in inputs["residual_events"] + inputs["scheduled_events"] if e.kind == "liability_charge"),
        Decimal("0"),
    )
    assert result.daily[-1].liability_balance == opening_owed + charged - paid
    cash_start = Decimal("5000.00")  # checking + savings
    cash_events = sum((e.amount for e in result.events if e.kind in {"residual", "scheduled_bill"}), Decimal("0"))
    assert result.daily[-1].ending_cash == cash_start + cash_events - paid


def test_a_recurring_bill_charged_to_a_settled_card_raises_the_balance_not_cash():
    streaming = [tx(date(2026, m, 9), -15.99, "STREAMCO", account="card") for m in (7, 8, 9, 10)]
    inputs = build(streaming + chk_noise(), rules=[payment_rule(amount=-300)])
    kinds = {e.kind for e in inputs["scheduled_events"]}
    assert "liability_charge" in kinds and "scheduled_bill" not in kinds
    charge = next(e for e in inputs["scheduled_events"] if e.kind == "liability_charge")
    assert charge.account_id == "card" and charge.amount == Decimal("15.99")

    proxy = build(streaming + chk_noise())
    assert any(e.kind == "scheduled_bill" and e.account_id is None for e in proxy["scheduled_events"])


def test_unknown_funding_keeps_the_checking_debit_as_cash_with_no_debt_reduction():
    # A checking debit to a card that has no linked destination stays an ordinary cash bill.
    ordinary = payment_rule(event_role="ordinary_expense", funding_account_id=None, destination_account_id=None)
    inputs = build(chk_noise(), rules=[ordinary])
    kinds = {e.kind for e in inputs["scheduled_events"]}
    assert kinds == {"scheduled_bill"}
    assert inputs["debt_payment_coverage"]["included"] == []
    result = simulate(inputs)
    assert result.daily[-1].liability_balance == Decimal("20000.00")


@pytest.mark.parametrize(
    "override",
    [
        {"funding_account_id": "card"},  # funded from a liability
        {"destination_account_id": "sav"},  # paying a deposit account
        {"destination_account_id": "ghost"},  # not in scope
        {"funding_account_id": None},
        {"funding_account_id": "chk", "destination_account_id": "chk"},
    ],
)
def test_a_payment_without_valid_cash_funding_and_liability_destination_is_never_invented(override):
    inputs = build(chk_noise(), rules=[payment_rule(**override)])
    cov = inputs["debt_payment_coverage"]
    assert cov["included"] == [] and cov["invalid_payment_stream_ids"] == ["stream:pay"]
    assert not [e for e in inputs["scheduled_events"] if e.kind == "liability_payment"]
    stream = next(s for s in inputs["streams"] if s["stream_id"] == "stream:pay")
    assert stream["status"] == "unsupported"


def test_loan_payments_mark_the_principal_split_unknown():
    inputs = build(chk_noise(), rules=[payment_rule(destination_account_id="loan", amount=-220)])
    payment = next(e for e in inputs["scheduled_events"] if e.kind == "liability_payment")
    assert payment.metadata["principal_split"] == "unknown" and payment.counterparty_account_id == "loan"
    card_payment = build(chk_noise(), rules=[payment_rule()])["scheduled_events"][0]
    assert card_payment.metadata["principal_split"] == "not_applicable"


def test_modes_report_settlement_proxy_or_mixed():
    only_card = [a for a in ACCOUNTS if a["account_id"] != "loan"]
    assert build(chk_noise(), accounts=only_card)["debt_payment_coverage"]["mode"] == "proxy"
    full = build(chk_noise(), accounts=only_card, rules=[payment_rule()])["debt_payment_coverage"]
    assert (full["mode"], full["unmodeled_account_count"], full["settled_account_ids"]) == ("settlement", 0, ["card"])
    assert build(chk_noise(), rules=[payment_rule()])["debt_payment_coverage"]["mode"] == "mixed"


def test_a_payment_larger_than_the_modeled_balance_floors_the_debt_at_zero():
    tiny = [{**a, "balance": 300} if a["account_id"] == "card" else a for a in ACCOUNTS]
    result = simulate(build(chk_noise(), rules=[payment_rule(amount=-500)], accounts=tiny), accounts=tiny)
    assert result.daily[-1].liability_balance == Decimal("8000.00")  # card floored at zero, loan untouched
    assert any(w["code"] == "liability_overpaid" for w in result.warnings)


def test_pending_rows_and_history_after_the_cutoff_cannot_leak_into_settlement():
    future = [tx(START + timedelta(days=3), -100, "Future Mart", account="card")]
    pending = [tx(AS_OF, -100, "Pending Mart", account="card", pending=True)]
    inputs = build(weekly_card_spend() + future + pending + chk_noise(), rules=[payment_rule(amount=-400)])
    audit = {e["transaction_id"]: e["bucket"] for e in inputs["allocation_audit"]}
    assert future[0]["transaction_id"] not in audit  # after the as-of date: not even audited
    assert audit[pending[0]["transaction_id"]] == "pending"

"""Forecast V2 sources: recurrence promotion, residual model and allocation audit."""

import json
import os
import sys
from datetime import date, timedelta
from decimal import Decimal

import pytest

BASE_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)

from forecast.v2_core import ForecastV2InputError, simulate_cash_ledger  # noqa: E402
from forecast.v2_sources import build_v2_inputs, normalize_merchant_key  # noqa: E402

AS_OF = date(2026, 10, 31)
START = date(2026, 11, 1)

ACCOUNTS = [
    {"account_id": "chk", "type": "depository", "subtype": "checking", "balance": 4000},
    {"account_id": "sav", "type": "depository", "subtype": "savings", "balance": 1000},
    {"account_id": "card", "type": "credit", "subtype": "credit card", "balance": 300},
]

_counter = {"n": 0}


def tx(day, amount, name, account="chk", **extra):
    _counter["n"] += 1
    return {
        "transaction_id": extra.pop("transaction_id", f"t{_counter['n']:05d}"),
        "account_id": account,
        "date": day.isoformat() if isinstance(day, date) else day,
        "amount": amount,
        "name": name,
        **extra,
    }


def every(start, step_days, until, amount, name, **extra):
    out, day = [], start
    while day <= until:
        out.append(tx(day, amount, name, **extra))
        day += timedelta(days=step_days)
    return out


def monthly(first, count, amount, name, **extra):
    out = []
    for i in range(count):
        month = first.month - 1 + i
        out.append(tx(date(first.year + month // 12, month % 12 + 1, first.day), amount, name, **extra))
    return out


def run(transactions, **kwargs):
    kwargs.setdefault("accounts", ACCOUNTS)
    return build_v2_inputs(
        transactions=transactions,
        as_of_date=AS_OF,
        start_date=START,
        horizon_days=kwargs.pop("horizon_days", 45),
        **kwargs,
    )


def audit_buckets(result):
    return {e["transaction_id"]: e["bucket"] for e in result["allocation_audit"]}


def groceries(until=AS_OF, days=90):
    """Irregular but frequent variable spending so the residual model has evidence."""
    out = []
    for offset in range(days):
        day = until - timedelta(days=offset)
        if offset % 3 == 0:
            out.append(tx(day, -20 - (offset % 7), f"Grocer {offset}"))
    return out


# ----------------------------------------------------------------------- recurrence


def test_biweekly_salary_becomes_one_event_stream_and_leaves_the_residual():
    salary = every(date(2026, 8, 7), 14, AS_OF, 2000, "ACME PAYROLL")
    result = run(salary + groceries())
    events = [e for e in result["scheduled_events"] if e.kind == "scheduled_income"]
    assert [e.date.isoformat() for e in events[:3]] == ["2026-11-13", "2026-11-27", "2026-12-11"]
    assert all(e.amount == Decimal("2000.00") for e in events)
    buckets = audit_buckets(result)
    assert all(buckets[t["transaction_id"]] == "scheduled" for t in salary)
    assert result["residual_model"]["income_by_weekday"] == {str(i): 0.0 for i in range(7)}
    (stream,) = [s for s in result["streams"] if s["kind"] == "income"]
    assert stream["status"] == "promoted" and stream["cadence"] == "biweekly"
    assert stream["confidence_level"] in {"medium", "high"}
    assert "calibrated" in stream["confidence_note"]


def test_monthly_rent_is_projected_once_per_month_not_daily():
    rent = monthly(date(2026, 8, 1), 3, -1850, "LANDLORD PROPERTIES")
    result = run(rent + groceries())
    bills = [e for e in result["scheduled_events"] if e.kind == "scheduled_bill"]
    assert [e.date.isoformat() for e in bills] == ["2026-11-01", "2026-12-01"]
    assert all(e.amount == Decimal("-1850.00") for e in bills)
    # Rent must not leak into the variable-spend average.
    assert result["residual_model"]["spend_by_weekday"]["0"] > -200


def test_scheduled_plus_residual_does_not_double_count_in_the_ledger():
    rent = monthly(date(2026, 8, 1), 3, -1000, "LANDLORD")
    history = rent + groceries()
    result = run(history, horizon_days=30)
    ledger = simulate_cash_ledger(
        start_date=START,
        horizon_days=30,
        account_snapshots=ACCOUNTS,
        events=result["scheduled_events"] + result["residual_events"],
    )
    scheduled_outflow = sum(e.amount for e in result["scheduled_events"] if e.amount < 0)
    residual_outflow = sum(e.amount for e in result["residual_events"] if e.amount < 0)
    assert ledger.summary["total_outflows"] == float(-(scheduled_outflow + residual_outflow))
    assert scheduled_outflow == Decimal("-1000.00")  # rent appears exactly once


def test_month_end_pay_and_weekend_shifted_deposits_are_still_monthly():
    pays = [
        tx("2026-07-31", 3000, "EMPLOYER"),
        tx("2026-08-31", 3000, "EMPLOYER"),
        tx("2026-09-30", 3000, "EMPLOYER"),
        tx("2026-10-30", 3000, "EMPLOYER"),  # 31st fell on a Saturday
    ]
    result = run(pays + groceries(), horizon_days=70)
    incomes = [e.date.isoformat() for e in result["scheduled_events"] if e.kind == "scheduled_income"]
    assert incomes[:2] == ["2026-11-30", "2026-12-31"]


def test_semimonthly_pay_detected_from_two_month_days():
    dates = [
        "2026-07-01",
        "2026-07-15",
        "2026-08-03",
        "2026-08-15",
        "2026-09-01",
        "2026-09-15",
        "2026-10-01",
        "2026-10-15",
    ]
    result = run([tx(d, 1500, "PAYCO") for d in dates] + groceries())
    (stream,) = [s for s in result["streams"] if s["kind"] == "income"]
    assert stream["cadence"] == "semimonthly" and stream["status"] == "promoted"
    assert [e.date.isoformat() for e in result["scheduled_events"][:3]] == ["2026-11-01", "2026-11-15", "2026-12-01"]


def test_a_lone_transaction_is_not_a_recurring_bill():
    lone = tx("2026-10-10", -500, "ONE OFF REPAIR")
    result = run([lone] + groceries())
    assert [e for e in result["scheduled_events"] if e.kind == "scheduled_bill"] == []
    assert audit_buckets(result)[lone["transaction_id"]] == "residual"


def test_two_occurrences_are_proposed_not_promoted_and_stay_in_residual():
    two = [tx("2026-09-05", -40, "NEWFLIX"), tx("2026-10-05", -40, "NEWFLIX")]
    result = run(two + groceries())
    assert result["scheduled_events"] == []
    (proposal,) = result["proposed_rules"]
    assert proposal["status"] == "proposed" and proposal["confidence_level"] == "low"
    assert {audit_buckets(result)[t["transaction_id"]] for t in two} == {"residual"}


def test_user_can_confirm_a_proposed_stream_and_disable_a_promoted_one():
    two = [tx("2026-09-05", -40, "NEWFLIX"), tx("2026-10-05", -40, "NEWFLIX")]
    proposal = run(two + groceries())["proposed_rules"][0]["stream_id"]
    confirmed = run(two + groceries(), confirmed_source_ids=[proposal])
    assert [e.date.isoformat() for e in confirmed["scheduled_events"][:2]] == ["2026-11-05", "2026-12-05"]
    assert all(audit_buckets(confirmed)[t["transaction_id"]] == "scheduled" for t in two)

    rent = monthly(date(2026, 8, 1), 3, -900, "LANDLORD")
    promoted = run(rent + groceries())
    stream_id = next(s["stream_id"] for s in promoted["streams"] if s["status"] == "promoted")
    disabled = run(rent + groceries(), disabled_source_ids=[stream_id])
    assert disabled["scheduled_events"] == []
    assert {audit_buckets(disabled)[t["transaction_id"]] for t in rent} == {"residual"}
    assert next(s for s in disabled["streams"] if s["stream_id"] == stream_id)["status"] == "disabled"


def test_manual_rule_takes_precedence_and_suppresses_duplicate_inference():
    rent = monthly(date(2026, 8, 1), 3, -1850, "LANDLORD PROPERTIES")
    rule = {
        "rule_id": "manual:rent",
        "account_id": "chk",
        "merchant_key": normalize_merchant_key(rent[0]),
        "amount": -1850,
        "cadence": "monthly",
        "anchor_date": "2026-11-01",
        "label": "Rent",
    }
    result = run(rent + groceries(), manual_rules=[rule])
    bills = [e for e in result["scheduled_events"] if e.kind == "scheduled_bill"]
    assert [e.source for e in bills] == ["manual", "manual"]
    assert [e.source_id for e in bills] == ["manual:rent", "manual:rent"]
    assert not [s for s in result["streams"] if s["origin"] == "inferred" and s["merchant_key"] == rule["merchant_key"]]
    assert {audit_buckets(result)[t["transaction_id"]] for t in rent} == {"scheduled"}


def test_saved_recurring_rule_with_unsupported_cadence_is_reported_not_guessed():
    rule = {
        "rule_id": "recurring:9",
        "account_id": "chk",
        "amount": -80,
        "cadence": "every_other_tuesday",
        "anchor_date": "2026-12-01",
    }
    result = run(groceries(), recurring_rules=[rule])
    stream = next(s for s in result["streams"] if s["stream_id"] == "recurring:9")
    assert stream["status"] == "unsupported" and "every_other_tuesday" in stream["reason"]
    assert result["scheduled_events"] == []


def test_two_subscriptions_to_the_same_merchant_stay_separate_but_dupes_collapse():
    small = monthly(date(2026, 8, 12), 3, -9.99, "STREAMCO")
    big = monthly(date(2026, 8, 20), 3, -25.00, "STREAMCO")
    dup = dict(small[0])  # same transaction_id imported twice
    result = run(small + big + [dup] + groceries())
    bills = [e for e in result["scheduled_events"] if e.kind == "scheduled_bill"]
    assert sorted({str(e.amount) for e in bills}) == ["-25.00", "-9.99"]
    assert len({e.source_id for e in bills}) == 2
    assert sum(1 for e in result["allocation_audit"] if e["bucket"] == "duplicate") == 1


def test_amount_jitter_is_median_based_and_streams_lapse_when_they_stop():
    jitter = [
        tx("2026-07-10", -52, "POWERCO"),
        tx("2026-08-10", -49, "POWERCO"),
        tx("2026-09-10", -55, "POWERCO"),
        tx("2026-10-10", -51, "POWERCO"),
    ]
    result = run(jitter + groceries())
    bills = [e for e in result["scheduled_events"] if e.kind == "scheduled_bill"]
    assert bills and all(e.amount == Decimal("-51.50") for e in bills)
    assert {audit_buckets(result)[t["transaction_id"]] for t in jitter} == {"scheduled"}

    cancelled = every(date(2026, 7, 6), 7, date(2026, 7, 27), -15, "OLDGYM")  # stopped in July
    lapsed = run(cancelled + groceries())
    assert lapsed["scheduled_events"] == []
    assert next(s for s in lapsed["streams"] if s["merchant_key"] == "oldgym")["status"] == "lapsed"


# ----------------------------------------------------------------------- transfers & pending


def test_transfers_and_card_payments_are_not_household_spending():
    history = groceries() + [
        tx("2026-10-02", -500, "Transfer to savings", transaction_id="a1", is_internal=True, internal_match_id="a2"),
        tx(
            "2026-10-02",
            500,
            "Transfer from checking",
            account="sav",
            transaction_id="a2",
            is_internal=True,
            internal_match_id="a1",
        ),
        tx("2026-10-20", -300, "Card payment", transaction_id="b1", is_internal=True, internal_match_id="b2"),
        tx(
            "2026-10-20",
            300,
            "Payment received",
            account="card",
            transaction_id="b2",
            is_internal=True,
            internal_match_id="b1",
        ),
        tx("2026-10-21", -75, "Restaurant", account="card", transaction_id="c1"),
    ]
    result = run(history)
    audit = {e["transaction_id"]: e for e in result["allocation_audit"]}
    assert audit["a1"]["transfer_kind"] == "cash_to_cash" and audit["a2"]["bucket"] == "transfer"
    assert audit["b1"]["transfer_kind"] == "liability_payment" and audit["b1"]["bucket"] == "transfer"
    assert audit["c1"]["bucket"] == "residual"  # card purchase is the cash-spend proxy
    assert result["reconciliation"]["by_bucket_amount"]["transfer"] == 0.0


def test_pending_rows_with_booked_equivalent_are_excluded():
    history = groceries() + [
        tx("2026-10-28", -33, "Cafe", transaction_id="p1", pending=True),
        tx("2026-10-29", -33, "Cafe", transaction_id="p2"),
        tx("2026-10-30", -12, "Bakery", transaction_id="p3", pending=True),
    ]
    audit = {e["transaction_id"]: e for e in run(history)["allocation_audit"]}
    assert audit["p1"]["bucket"] == "pending" and audit["p1"]["reason"] == "booked_equivalent_exists"
    assert audit["p2"]["bucket"] == "residual"
    assert audit["p3"]["bucket"] == "pending" and audit["p3"]["reason"] == "not_posted_yet"


# ----------------------------------------------------------------------- residual model


def test_residual_uses_complete_days_and_winsorizes_outliers():
    mondays = [date(2026, 8, 3) + timedelta(days=7 * i) for i in range(13)]
    base = [tx(day, -30, f"Shop{chr(65 + i)}") for i, day in enumerate(mondays)]  # Mondays, varied merchants
    spike = [tx("2026-09-14", -5000, "Furniture")]
    result = run(base + spike)
    model = result["residual_model"]
    assert model["status"] == "ok"
    assert model["spend_by_weekday"]["1"] == 0.0  # zero-spend weekdays stay zero
    monday = model["spend_by_weekday"]["0"]
    assert -35 < monday < -5  # outlier clipped well below the raw 5000 spike
    assert result["coverage"]["history_days"] == (AS_OF - date(2026, 8, 3)).days + 1


def test_sparse_history_is_flagged_and_yields_no_fabricated_pattern():
    result = run([tx("2026-10-28", -20, "Snack"), tx("2026-10-30", -10, "Snack2")])
    assert result["coverage"]["residual_model"] == "insufficient_history"
    assert result["coverage"]["confidence"] == "insufficient"
    assert result["residual_events"] == []


def test_residual_income_is_kept_separate_from_spending():
    refunds = every(date(2026, 8, 5), 9, AS_OF, 15, "Venmo cashout")
    result = run(groceries() + refunds)
    components = {e.metadata["component"] for e in result["residual_events"]}
    assert components == {"spend", "income"}
    assert all(e.amount > 0 for e in result["residual_events"] if e.metadata["component"] == "income")
    assert all(e.amount < 0 for e in result["residual_events"] if e.metadata["component"] == "spend")


# ----------------------------------------------------------------------- scope & audit


def test_future_and_foreign_transactions_cannot_influence_the_forecast():
    history = groceries()
    clean = run(history)
    tainted = run(
        history
        + [
            tx("2026-11-15", -9999, "Future"),
            tx("2026-10-15", -7777, "Other user's", account="someone-elses-account"),
        ]
    )
    assert clean["residual_model"] == tainted["residual_model"]
    assert tainted["reconciliation"]["rejected"]["after_as_of"] == 1
    assert tainted["reconciliation"]["rejected"]["foreign_account"] == 1
    assert len(tainted["allocation_audit"]) == len(clean["allocation_audit"])


def test_every_in_scope_transaction_is_audited_exactly_once_and_reconciles():
    rent = monthly(date(2026, 8, 1), 3, -1850, "LANDLORD")
    pay = every(date(2026, 8, 7), 14, AS_OF, 2000, "PAYROLL")
    odd = [tx("2026-10-02", -5, "x", is_internal=True), tx("2026-10-03", -6, "Cafe", pending=True)]
    history = rent + pay + groceries() + odd
    result = run(history)
    recon = result["reconciliation"]
    assert recon["in_scope_transactions"] == recon["audited_transactions"] == len(history)
    assert sum(recon["by_bucket_count"].values()) == len(history)
    ids = [e["transaction_id"] for e in result["allocation_audit"]]
    assert len(ids) == len(set(ids)) == len(history)
    expected_total = sum(Decimal(str(t["amount"])) for t in history)
    assert sum(Decimal(e["amount"]) for e in result["allocation_audit"]) == expected_total


def test_non_cash_account_transactions_are_unclassified_not_dropped():
    accounts = ACCOUNTS + [{"account_id": "brk", "type": "investment", "subtype": "brokerage", "balance": 10}]
    result = run(
        groceries() + [tx("2026-10-02", -250, "ETF buy", account="brk", transaction_id="inv1")], accounts=accounts
    )
    entry = next(e for e in result["allocation_audit"] if e["transaction_id"] == "inv1")
    assert entry["bucket"] == "unclassified" and entry["reason"] == "non_cash_account"


def test_outputs_are_deterministic_and_secret_free():
    history = monthly(date(2026, 8, 1), 3, -1850, "LANDLORD") + groceries()

    def snapshot(rows):
        result = run(rows)
        return json.dumps(
            {
                "scheduled": [e.to_dict() for e in result["scheduled_events"]],
                "residual": [e.to_dict() for e in result["residual_events"]],
                "audit": result["allocation_audit"],
                "streams": result["streams"],
                "coverage": result["coverage"],
            },
            sort_keys=True,
        )

    assert snapshot(history) == snapshot(history[::-1])
    assert "access_token" not in snapshot(history)


def test_invalid_inputs_raise_explicit_errors():
    with pytest.raises(ForecastV2InputError) as error:
        build_v2_inputs(transactions=[], accounts=ACCOUNTS, as_of_date=AS_OF, start_date=AS_OF, horizon_days=10)
    assert error.value.code == "invalid_range"
    with pytest.raises(ForecastV2InputError):
        build_v2_inputs(transactions=[], accounts=ACCOUNTS, as_of_date=AS_OF, start_date=START, horizon_days=0)


def test_full_pipeline_feeds_the_v2_simulator_without_warnings_about_dropped_events():
    history = (
        monthly(date(2026, 8, 1), 3, -1850, "LANDLORD")
        + every(date(2026, 8, 7), 14, AS_OF, 2000, "PAYROLL")
        + groceries()
    )
    result = run(history, horizon_days=60)
    ledger = simulate_cash_ledger(
        start_date=START,
        horizon_days=60,
        account_snapshots=ACCOUNTS,
        events=result["scheduled_events"] + result["residual_events"],
    )
    assert ledger.status == "ok"
    assert not [w for w in ledger.warnings if w["code"].startswith("event_")]
    assert len(ledger.daily) == 60

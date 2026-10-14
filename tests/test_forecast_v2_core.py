"""Forecast V2 core: event ledger, account buckets and calendar recurrence."""

import json
import os
import sys
from datetime import date
from decimal import Decimal

import pytest

BASE_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)

from forecast.models import ForecastV2Event  # noqa: E402
from forecast.v2_core import (  # noqa: E402
    ForecastV2InputError,
    classify_forecast_account,
    expand_scheduled_events,
    simulate_cash_ledger,
)

START = date(2026, 11, 1)


def acct(account_id, acct_type, balance, subtype=None, **extra):
    return {"account_id": account_id, "type": acct_type, "subtype": subtype, "balance": balance, **extra}


def standard_accounts():
    return [
        acct("checking", "depository", 3000, "checking"),
        acct("savings", "depository", 2000, "savings"),
        acct("cash", "cash", 100),
        acct("visa", "credit", 1200, "credit card"),
        acct("auto", "loan", 3000, "auto"),
        acct("brokerage", "investment", 5000, "brokerage"),
    ]


def event(day, amount, kind, account_id="checking", source_id=None, **extra):
    source_id = source_id or f"{kind}-{day}"
    return {
        "date": day,
        "amount": amount,
        "kind": kind,
        "account_id": account_id,
        "source_id": source_id,
        "source": "test",
        **extra,
    }


def assert_invariants(result):
    previous_end = None
    for point in result.daily:
        assert point.ending_cash == point.starting_cash + point.inflows - point.outflows + point.adjustments
        assert (
            point.net_worth == point.ending_cash + point.other_assets + point.investment_value - point.liability_balance
        )
        assert sum(point.cash_by_account.values()) == point.ending_cash
        if previous_end is not None:
            assert point.starting_cash == previous_end
        previous_end = point.ending_cash


# ----------------------------------------------------------------------- accounts


def test_buckets_partition_cash_debt_and_investments():
    result = simulate_cash_ledger(start_date=START, horizon_days=3, account_snapshots=standard_accounts())
    first = result.daily[0]
    assert first.starting_cash == Decimal("5100.00")
    assert first.liability_balance == Decimal("4200.00")
    assert first.investment_value == Decimal("5000.00")
    assert first.net_worth == Decimal("5100.00") + Decimal("5000.00") - Decimal("4200.00")
    assert first.ending_cash != first.net_worth
    assert result.accounts["included"]["cash"] == ["cash", "checking", "savings"]
    assert result.accounts["included"]["liability"] == ["auto", "visa"]


def test_subset_of_accounts_changes_only_matching_buckets():
    subset = [a for a in standard_accounts() if a["account_id"] not in {"savings", "brokerage"}]
    result = simulate_cash_ledger(start_date=START, horizon_days=1, account_snapshots=subset)
    point = result.daily[0]
    assert point.starting_cash == Decimal("3100.00")
    assert point.investment_value == Decimal("0.00")
    assert point.liability_balance == Decimal("4200.00")


@pytest.mark.parametrize(
    "account,bucket",
    [
        ({"type": "depository", "subtype": "checking"}, "cash"),
        ({"type": "depository", "subtype": "savings"}, "cash"),
        ({"type": "Checking"}, "cash"),
        ({"type": "credit", "subtype": "credit card"}, "liability"),
        ({"type": "loan", "subtype": "mortgage"}, "liability"),
        ({"type": "investment", "subtype": "401k"}, "investment"),
        ({"type": "depository", "subtype": "cd", "is_investment": False}, "unknown"),
        ({"type": "other"}, "unknown"),
        ({"type": "real estate"}, "other_asset"),
        ({}, "unknown"),
    ],
)
def test_classify_forecast_account(account, bucket):
    assert classify_forecast_account(account) == bucket


def test_unknown_hidden_and_foreign_accounts_are_excluded_with_warnings():
    accounts = standard_accounts() + [
        acct("mystery", "other", 999),
        acct("hidden", "depository", 777, "checking", is_hidden=True),
        acct("theirs", "depository", 555, "checking", user_id="someone-else"),
        acct("mine", "depository", 10, "checking", user_id="owner"),
    ]
    result = simulate_cash_ledger(start_date=START, horizon_days=1, account_snapshots=accounts, owner_id="owner")
    assert result.daily[0].starting_cash == Decimal("5110.00")
    codes = {(w["code"], w.get("account_id")) for w in result.warnings}
    assert ("unknown_account_type", "mystery") in codes
    assert ("account_hidden", "hidden") in codes
    assert ("account_not_authorized", "theirs") in codes
    assert set(result.accounts["excluded"]) == {"mystery", "hidden", "theirs"}


def test_no_eligible_cash_account_is_explicit():
    result = simulate_cash_ledger(
        start_date=START, horizon_days=5, account_snapshots=[acct("visa", "credit", 100, "credit card")]
    )
    assert result.status == "insufficient_data"
    assert result.daily == []
    assert [w["code"] for w in result.warnings] == ["no_liquid_cash_accounts"]


def test_stale_and_missing_balance_are_flagged():
    accounts = [
        acct("checking", "depository", 100, "checking", as_of="2026-10-01"),
        acct("nobal", "depository", None, "savings"),
    ]
    result = simulate_cash_ledger(start_date=START, horizon_days=1, account_snapshots=accounts)
    codes = {w["code"] for w in result.warnings}
    assert {"stale_snapshot", "missing_balance"} <= codes


# ----------------------------------------------------------------------- ledger


def test_day_zero_anchor_zero_event_days_and_each_event_applies_once():
    events = [
        event("2026-11-01", "-1850.00", "scheduled_bill", source_id="rent"),
        event("2026-11-03", "2000.00", "scheduled_income", source_id="pay"),
    ]
    result = simulate_cash_ledger(
        start_date=START,
        horizon_days=5,
        account_snapshots=[acct("checking", "depository", 3000, "checking")],
        events=events,
    )
    assert [p.date.day for p in result.daily] == [1, 2, 3, 4, 5]
    assert [p.ending_cash for p in result.daily] == [
        Decimal(x) for x in ("1150.00", "1150.00", "3150.00", "3150.00", "3150.00")
    ]
    assert result.daily[0].starting_cash == Decimal("3000.00")
    assert result.daily[1].event_ids == [] and result.daily[1].inflows == 0
    assert len(result.events) == 2
    assert result.summary["first_negative_date"] is None
    assert result.summary["min_cash"] == 1150.0 and result.summary["min_cash_date"] == "2026-11-01"
    assert_invariants(result)


def test_first_negative_date_and_cent_exact_totals():
    result = simulate_cash_ledger(
        start_date=START,
        horizon_days=4,
        account_snapshots=[acct("checking", "depository", "100.10", "checking")],
        events=[event("2026-11-02", "-0.15", "scheduled_bill"), event("2026-11-03", "-100.00", "scheduled_bill")],
    )
    assert result.summary["first_negative_date"] == "2026-11-03"
    assert result.summary["total_outflows"] == 100.15
    assert result.summary["ending_cash"] == -0.05
    assert_invariants(result)


def test_cash_to_cash_transfer_has_no_consolidated_effect():
    result = simulate_cash_ledger(
        start_date=START,
        horizon_days=2,
        account_snapshots=standard_accounts(),
        events=[event("2026-11-01", "500", "transfer", "checking", counterparty_account_id="savings")],
    )
    day = result.daily[0]
    assert day.starting_cash == day.ending_cash
    assert day.inflows == 0 and day.outflows == 0
    assert day.cash_by_account["checking"] == Decimal("2500.00")
    assert day.cash_by_account["savings"] == Decimal("2500.00")
    assert_invariants(result)


def test_credit_card_payment_lowers_cash_and_debt_but_not_net_worth():
    result = simulate_cash_ledger(
        start_date=START,
        horizon_days=2,
        account_snapshots=standard_accounts(),
        events=[event("2026-11-01", "400", "liability_payment", "checking", counterparty_account_id="visa")],
    )
    first = result.daily[0]
    assert first.ending_cash == Decimal("4700.00")
    assert first.liability_balance == Decimal("3800.00")
    assert first.net_worth == result.summary["starting_net_worth"] == float(first.net_worth)
    assert first.outflows == Decimal("400.00")
    assert_invariants(result)


def test_overpaying_a_liability_floors_it_and_warns():
    result = simulate_cash_ledger(
        start_date=START,
        horizon_days=1,
        account_snapshots=standard_accounts(),
        events=[event("2026-11-01", "5000", "liability_payment", "checking", counterparty_account_id="visa")],
    )
    assert result.daily[0].liability_balance == Decimal("3000.00")
    assert "liability_overpaid" in {w["code"] for w in result.warnings}
    assert_invariants(result)


def test_credit_purchase_is_not_a_cash_event_until_paid():
    result = simulate_cash_ledger(
        start_date=START,
        horizon_days=3,
        account_snapshots=standard_accounts(),
        events=[
            event("2026-11-01", "250", "liability_charge", "visa"),
            event("2026-11-03", "250", "liability_payment", "checking", counterparty_account_id="visa"),
        ],
    )
    first, second, third = result.daily
    assert first.ending_cash == first.starting_cash and first.liability_balance == Decimal("4450.00")
    assert first.net_worth == second.net_worth == Decimal("5100.00") + Decimal("5000.00") - Decimal("4450.00")
    assert third.ending_cash == Decimal("4850.00") and third.liability_balance == Decimal("4200.00")
    assert_invariants(result)


def test_investment_contribution_moves_value_between_buckets():
    result = simulate_cash_ledger(
        start_date=START,
        horizon_days=1,
        account_snapshots=standard_accounts(),
        events=[event("2026-11-01", "1000", "transfer", "checking", counterparty_account_id="brokerage")],
    )
    point = result.daily[0]
    assert point.ending_cash == Decimal("4100.00") and point.investment_value == Decimal("6000.00")
    assert point.net_worth == Decimal("4100.00") + Decimal("6000.00") - Decimal("4200.00")
    assert_invariants(result)


def test_events_for_non_cash_or_unscoped_accounts_are_dropped_with_warnings():
    result = simulate_cash_ledger(
        start_date=START,
        horizon_days=1,
        account_snapshots=standard_accounts(),
        events=[
            event("2026-11-01", "-50", "scheduled_bill", "visa", source_id="x"),
            event("2026-11-01", "-60", "scheduled_bill", "not-mine", source_id="y"),
        ],
    )
    assert result.events == []
    assert [w["code"] for w in result.warnings].count("event_account_not_cash") == 2
    assert result.daily[0].ending_cash == result.daily[0].starting_cash


# ----------------------------------------------------------------------- recurrence


def dates(events):
    return [e.date.isoformat() for e in events]


def rule(cadence, anchor, **extra):
    return {
        "source_id": "r",
        "source": "recurring",
        "kind": "scheduled_bill",
        "amount": "-10",
        "account_id": "checking",
        "cadence": cadence,
        "anchor_date": anchor,
        **extra,
    }


def test_monthly_day_31_clamps_and_returns_to_anchor_across_leap_and_year_end():
    out = expand_scheduled_events([rule("monthly", "2027-12-31")], "2027-12-01", "2028-04-30")
    assert dates(out) == ["2027-12-31", "2028-01-31", "2028-02-29", "2028-03-31", "2028-04-30"]
    non_leap = expand_scheduled_events([rule("monthly", "2026-01-31")], "2026-01-01", "2026-04-30")
    assert dates(non_leap) == ["2026-01-31", "2026-02-28", "2026-03-31", "2026-04-30"]


def test_weekly_biweekly_daily_do_not_drift_and_start_at_the_anchor():
    assert dates(expand_scheduled_events([rule("weekly", "2026-10-26")], "2026-11-01", "2026-11-22")) == [
        "2026-11-02",
        "2026-11-09",
        "2026-11-16",
    ]
    biweekly = expand_scheduled_events([rule("biweekly", "2026-10-30")], "2026-11-01", "2026-12-31")
    assert dates(biweekly) == ["2026-11-13", "2026-11-27", "2026-12-11", "2026-12-25"]
    assert len(expand_scheduled_events([rule("daily", "2026-11-03")], "2026-11-01", "2026-11-05")) == 3


def test_semimonthly_uses_two_explicit_days_and_clamps_short_months():
    out = expand_scheduled_events([rule("semimonthly", "2027-01-01", days=[15, 31])], "2027-01-01", "2027-03-31")
    assert dates(out) == [
        "2027-01-15",
        "2027-01-31",
        "2027-02-15",
        "2027-02-28",
        "2027-03-15",
        "2027-03-31",
    ]
    both_clamp = expand_scheduled_events([rule("semimonthly", "2027-01-01", days=[30, 31])], "2027-02-01", "2027-02-28")
    assert [e.event_id for e in both_clamp] == ["recurring:r:2027-02-28", "recurring:r:2027-02-28#2"]


def test_effective_end_date_and_horizon_bound_events():
    out = expand_scheduled_events([rule("monthly", "2026-11-05", end_date="2027-01-05")], "2026-11-01", "2027-06-30")
    assert dates(out) == ["2026-11-05", "2026-12-05", "2027-01-05"]
    assert expand_scheduled_events([rule("once", "2026-10-01")], "2026-11-01", "2026-11-30") == []


@pytest.mark.parametrize(
    "spec,code",
    [
        (rule("fortnightly", "2026-11-01"), "invalid_cadence"),
        (rule("monthly", "not-a-date"), "invalid_date"),
        (rule("monthly", "2026-11-01", end_date="2026-10-01"), "invalid_range"),
        (rule("semimonthly", "2026-11-01"), "invalid_semimonthly_days"),
        (rule("semimonthly", "2026-11-01", days=[5, 5]), "invalid_semimonthly_days"),
        (rule("monthly", "2026-11-01", amount="abc"), "invalid_amount"),
        (rule("monthly", "2026-11-01", amount="10"), "invalid_amount"),
        (rule("monthly", "2026-11-01", kind="mystery"), "invalid_kind"),
    ],
)
def test_invalid_rules_raise_specific_errors(spec, code):
    with pytest.raises(ForecastV2InputError) as error:
        expand_scheduled_events([spec], "2026-11-01", "2026-12-31")
    assert error.value.code == code


@pytest.mark.parametrize("horizon", [0, -3, 5000, "7", True])
def test_invalid_horizon_is_rejected(horizon):
    with pytest.raises(ForecastV2InputError) as error:
        simulate_cash_ledger(start_date=START, horizon_days=horizon, account_snapshots=standard_accounts())
    assert error.value.code == "invalid_horizon"


def test_invalid_start_date_is_rejected():
    with pytest.raises(ForecastV2InputError) as error:
        simulate_cash_ledger(start_date="soon", horizon_days=3, account_snapshots=standard_accounts())
    assert error.value.code == "invalid_date"


# ----------------------------------------------------------------------- adjustments & dedupe


def test_manual_adjustments_apply_once_and_keep_invariants():
    result = simulate_cash_ledger(
        start_date=START,
        horizon_days=10,
        account_snapshots=[acct("checking", "depository", 1000, "checking")],
        cash_adjustments=[
            {"adjustment_id": "once", "amount": -100, "date": "2026-11-02", "frequency": "once"},
            {"adjustment_id": "weekly", "amount": 25, "date": "2026-11-01", "frequency": "weekly"},
            {
                "adjustment_id": "spread",
                "amount": -100,
                "distribution": "spread",
                "range_start": "2026-11-05",
                "range_end": "2026-11-07",
            },
        ],
    )
    assert result.summary["total_adjustments"] == -100 + 50 - 100
    assert sum(p.adjustments for p in result.daily) == Decimal("-150.00")
    spread = [p.adjustments for p in result.daily if p.date.day in {5, 6, 7}]
    assert spread == [Decimal("-33.33"), Decimal("-33.33"), Decimal("-33.34")]
    assert result.daily[1].adjustments == Decimal("-100.00")
    assert result.summary["by_kind"]["adjustment"] == -150.0
    assert_invariants(result)


def test_spread_adjustment_preserves_total_to_the_cent():
    result = simulate_cash_ledger(
        start_date=START,
        horizon_days=3,
        account_snapshots=[acct("checking", "depository", 0, "checking")],
        cash_adjustments=[
            {
                "adjustment_id": "s",
                "amount": "100.00",
                "distribution": "spread",
                "range_start": "2026-11-01",
                "range_end": "2026-11-03",
            }
        ],
    )
    assert [p.adjustments for p in result.daily] == [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]
    assert_invariants(result)


def test_duplicate_event_ids_dedupe_but_distinct_same_day_events_remain():
    twin = event("2026-11-02", "-40", "scheduled_bill", source_id="gym", event_id="recurring:gym:2026-11-02")
    result = simulate_cash_ledger(
        start_date=START,
        horizon_days=3,
        account_snapshots=[acct("checking", "depository", 500, "checking")],
        events=[
            twin,
            dict(twin),
            event("2026-11-02", "-40", "scheduled_bill", source_id="other-gym"),
            {"date": "2026-11-02", "amount": "-5", "kind": "scheduled_bill", "account_id": "checking"},
            {"date": "2026-11-02", "amount": "-5", "kind": "scheduled_bill", "account_id": "checking"},
        ],
    )
    assert result.daily[1].outflows == Decimal("90.00")
    assert len(result.events) == 4
    assert "duplicate_event_dropped" in {w["code"] for w in result.warnings}


def test_override_replaces_scheduled_instance_without_double_applying():
    scheduled = event("2026-11-02", "-1000", "scheduled_bill", source_id="rent", event_id="recurring:rent:2026-11-02")
    manual = {**scheduled, "amount": "-900", "override": True}
    for ordering in ([scheduled, manual], [manual, scheduled]):
        result = simulate_cash_ledger(
            start_date=START,
            horizon_days=3,
            account_snapshots=[acct("checking", "depository", 2000, "checking")],
            events=ordering,
        )
        assert result.daily[1].outflows == Decimal("900.00")
        assert len(result.events) == 1


def test_recurrence_specs_and_concrete_events_mix_in_one_run():
    result = simulate_cash_ledger(
        start_date=START,
        horizon_days=40,
        account_snapshots=[acct("checking", "depository", 5000, "checking")],
        events=[rule("monthly", "2026-11-05", amount="-100"), event("2026-11-10", "300", "scheduled_income")],
    )
    assert result.summary["event_count"] == 3  # Nov 5, Nov 10, Dec 5
    assert result.summary["total_outflows"] == 200.0
    assert_invariants(result)


def test_events_outside_horizon_are_counted_not_applied():
    result = simulate_cash_ledger(
        start_date=START,
        horizon_days=3,
        account_snapshots=[acct("checking", "depository", 100, "checking")],
        events=[event("2026-10-31", "-50", "scheduled_bill"), event("2026-11-04", "-50", "scheduled_bill")],
    )
    assert result.summary["events_outside_horizon"] == 2
    assert result.summary["ending_cash"] == 100.0


# ----------------------------------------------------------------------- determinism & safety


def run_for_serialization(reverse=False):
    events = [
        rule("monthly", "2026-11-05", amount="-100"),
        event("2026-11-10", "300", "scheduled_income", source_id="pay"),
        event("2026-11-12", "-40", "scheduled_bill", source_id="a"),
        event("2026-11-12", "-41", "scheduled_bill", source_id="b"),
    ]
    accounts = standard_accounts()
    if reverse:
        events, accounts = events[::-1], accounts[::-1]
    return simulate_cash_ledger(start_date=START, horizon_days=45, account_snapshots=accounts, events=events).to_dict()


def test_identical_inputs_serialize_identically_regardless_of_input_order():
    one = json.dumps(run_for_serialization(), sort_keys=True)
    two = json.dumps(run_for_serialization(), sort_keys=True)
    shuffled = json.dumps(run_for_serialization(reverse=True), sort_keys=True)
    assert one == two == shuffled


def test_event_provenance_is_traceable_and_secrets_are_scrubbed():
    result = simulate_cash_ledger(
        start_date=START,
        horizon_days=2,
        account_snapshots=[acct("checking", "depository", 100, "checking")],
        events=[
            event(
                "2026-11-01",
                "-5",
                "scheduled_bill",
                source_id="netflix",
                confidence=0.9,
                metadata={"category": "media", "access_token": "secret", "nested": {"item_id": "x", "keep": 1}},
            )
        ],
    )
    (payload,) = result.to_dict()["events"]
    assert payload["amount"] == "-5.00"
    assert payload["source_id"] == "netflix" and payload["confidence"] == 0.9
    assert payload["metadata"] == {"category": "media", "nested": {"keep": 1}}
    assert result.to_dict()["daily"][0]["event_ids"] == [payload["event_id"]]
    assert "secret" not in json.dumps(result.to_dict())


def test_prebuilt_event_objects_are_accepted():
    prebuilt = ForecastV2Event(
        event_id="manual:x:2026-11-01",
        date=START,
        amount=Decimal("-12.00"),
        account_id="checking",
        kind="scheduled_bill",
    )
    result = simulate_cash_ledger(
        start_date=START,
        horizon_days=1,
        account_snapshots=[acct("checking", "depository", 100, "checking")],
        events=[prebuilt],
    )
    assert result.summary["ending_cash"] == 88.0


def test_events_without_a_funding_account_hit_consolidated_cash_only():
    result = simulate_cash_ledger(
        start_date=START,
        horizon_days=2,
        account_snapshots=[acct("checking", "depository", 100, "checking")],
        events=[
            {
                "date": "2026-11-01",
                "amount": "-30",
                "kind": "scheduled_bill",
                "account_id": None,
                "source_id": "card-sub",
            },
            {"date": "2026-11-02", "amount": "-5", "kind": "residual", "account_id": None, "source_id": "spend"},
        ],
    )
    assert result.summary["ending_cash"] == 65.0
    assert result.daily[1].cash_by_account["unassigned"] == Decimal("-35.00")
    assert_invariants(result)

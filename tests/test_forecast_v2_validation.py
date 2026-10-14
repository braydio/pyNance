"""Forecast V2 validation: leakage-safe rolling backtests and honest scoring."""

import copy
import json
import os
import sys
from datetime import date, timedelta
from decimal import Decimal

import pytest

BASE_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)

from forecast.v2_core import ForecastV2InputError  # noqa: E402
from forecast.v2_validation import backtest_v2, history_loaders  # noqa: E402

WORLD_START = date(2026, 1, 1)
WORLD_END = date(2026, 10, 31)
ACCOUNTS = [{"account_id": "chk", "type": "depository", "subtype": "checking"}]
WEEKDAY_SPEND = {0: -24, 1: -0, 2: -31, 3: -0, 4: -45, 5: -60, 6: -12}


def build_world(*, jitter=False, opening="3000.00"):
    """Daily world with biweekly payroll, monthly rent and fixed weekday spending, plus EOD snapshots."""
    transactions, n = [], 0

    def add(day, amount, name):
        nonlocal n
        n += 1
        transactions.append(
            {
                "transaction_id": f"w{n:05d}",
                "account_id": "chk",
                "date": day.isoformat(),
                "amount": amount,
                "name": name,
            }
        )

    balance, snapshots = Decimal(opening), []
    pay_day = date(2026, 1, 2)
    paychecks = 0
    for offset in range((WORLD_END - WORLD_START).days + 1):
        day = WORLD_START + timedelta(days=offset)
        delta = Decimal("0")
        if (day - pay_day).days % 14 == 0:
            paychecks += 1
            amount = 2000 + (100 if jitter and paychecks % 2 else 0)
            shift = timedelta(days=-1 if jitter and day.weekday() == 4 and paychecks % 3 == 0 else 0)
            add(day + shift if shift else day, amount, "ACME PAYROLL")
            delta += amount
        if day.day == 1:
            add(day, -1200, "LANDLORD PROPERTIES")
            delta -= 1200
        spend = WEEKDAY_SPEND[day.weekday()]
        if spend:
            add(day, spend, f"Shop{day.weekday()}")
            delta += spend
        balance += delta
        snapshots.append({"account_id": "chk", "date": day.isoformat(), "balance": str(balance)})
    return transactions, snapshots


CUTOFFS = [date(2026, 8, 31) + timedelta(days=7 * i) for i in range(5)]


def run(world=None, **kwargs):
    transactions, snapshots = world or build_world()
    loaders = history_loaders(accounts=ACCOUNTS, transactions=transactions, snapshots=snapshots)
    kwargs.setdefault("cutoffs", CUTOFFS)
    return backtest_v2(load_inputs=loaders[0], load_truth=loaders[1], load_realized=loaders[2], **kwargs)


# ----------------------------------------------------------------------- leakage


def test_future_data_cannot_change_a_forecast_made_at_the_cutoff():
    cutoff = date(2026, 9, 14)
    transactions, snapshots = build_world()
    baseline = run((transactions, snapshots), cutoffs=[cutoff]).to_dict()

    mutated_tx = copy.deepcopy(transactions)
    for tx in mutated_tx:
        if date.fromisoformat(tx["date"]) > cutoff:
            tx["amount"] = tx["amount"] * 10 - 500
    mutated_tx.append(
        {"transaction_id": "leak", "account_id": "chk", "date": "2026-09-20", "amount": -99999, "name": "Leak"}
    )
    mutated_snaps = copy.deepcopy(snapshots)
    for snap in mutated_snaps:
        if date.fromisoformat(snap["date"]) > cutoff:
            snap["balance"] = "-12345.00"
    changed = run((mutated_tx, mutated_snaps), cutoffs=[cutoff]).to_dict()

    assert baseline["folds"][0]["status"] == "evaluated"
    for key in ("7", "14", "30"):
        assert (
            baseline["folds"][0]["predictions"][key]["predicted"]
            == changed["folds"][0]["predictions"][key]["predicted"]
        )
    # ...while the realized truth did change, proving the mutation was visible to scoring.
    assert baseline["balance"] != changed["balance"]


def test_todays_balance_is_never_used_at_a_historical_cutoff():
    transactions, snapshots = build_world()
    loaders = history_loaders(accounts=ACCOUNTS, transactions=transactions, snapshots=snapshots)
    inputs = loaders[0](date(2026, 9, 14))
    (account,) = inputs["accounts"]
    assert account["as_of"] == date(2026, 9, 14)
    assert account["balance"] == Decimal(next(s["balance"] for s in snapshots if s["date"] == "2026-09-14"))


# ----------------------------------------------------------------------- scoring


def constant_loaders(snapshots):
    """Loaders over a quiet account (no transactions) so predictions equal the anchor balance."""
    return history_loaders(accounts=ACCOUNTS, transactions=[], snapshots=snapshots)


def snaps(cutoff, values):
    return [
        {"account_id": "chk", "date": (cutoff + timedelta(days=offset)).isoformat(), "balance": str(value)}
        for offset, value in values.items()
    ]


def test_mae_bias_and_missing_truth_counts_are_exact():
    cutoff = date(2026, 6, 1)
    snapshots = snaps(cutoff, {0: "1000.00", 7: "950.00", 14: "900.00"})  # no day-30 truth
    loaders = constant_loaders(snapshots)
    report = backtest_v2(cutoffs=[cutoff], load_inputs=loaders[0], load_truth=loaders[1])
    assert report.balance["7"] == {"samples": 1, "mae": 50.0, "bias": 50.0}  # predicted 1000 - actual 950
    assert report.balance["14"] == {"samples": 1, "mae": 100.0, "bias": 100.0}
    assert report.balance["30"] == {"samples": 0, "mae": None, "bias": None}
    assert report.skipped == {"missing_truth_horizons": 1}
    assert report.folds_evaluated == 1


def test_signed_bias_reports_under_forecasting_with_a_negative_sign():
    cutoff = date(2026, 6, 1)
    snapshots = snaps(cutoff, {0: "1000.00", 7: "1100.00", 14: "1000.00", 30: "1000.00"})
    loaders = constant_loaders(snapshots)
    report = backtest_v2(cutoffs=[cutoff], load_inputs=loaders[0], load_truth=loaders[1])
    assert report.balance["7"]["bias"] == -100.0 and report.balance["7"]["mae"] == 100.0
    assert report.balance["14"]["mae"] == 0.0


def test_folds_without_a_fresh_anchor_or_truth_are_skipped_with_reasons():
    cutoff = date(2026, 6, 1)
    stale = snaps(cutoff, {-5: "1000.00", 7: "950.00"})
    loaders = constant_loaders(stale)
    report = backtest_v2(cutoffs=[cutoff], load_inputs=loaders[0], load_truth=loaders[1])
    assert report.skipped == {"stale_anchor": 1} and report.folds_evaluated == 0

    none = constant_loaders([])
    missing = backtest_v2(cutoffs=[cutoff], load_inputs=none[0], load_truth=none[1])
    assert missing.skipped == {"no_anchor_snapshot": 1}

    anchor_only = constant_loaders(snaps(cutoff, {0: "1000.00"}))
    no_truth = backtest_v2(cutoffs=[cutoff], load_inputs=anchor_only[0], load_truth=anchor_only[1])
    assert no_truth.skipped["no_truth_in_window"] == 1 and no_truth.folds_evaluated == 0


def test_regular_payroll_and_rent_have_zero_timing_and_amount_error():
    report = run()
    assert report.folds_evaluated == len(CUTOFFS)
    recurring = report.recurring
    assert recurring["matched"] >= len(CUTOFFS)  # at least rent or payroll per fold
    assert recurring["date_error_mae_days"] == 0.0 and recurring["amount_error_mae"] == 0.0
    assert recurring["missed"] == 0
    assert all(report.balance[h]["samples"] == len(CUTOFFS) for h in ("7", "14", "30"))
    assert report.balance["7"]["mae"] < report.balance["30"]["mae"] + 1  # error grows with horizon, sanity


def test_irregular_payroll_produces_measured_nonzero_errors():
    report = run(build_world(jitter=True))
    recurring = report.recurring
    assert recurring["matched"] > 0
    assert (recurring["date_error_mae_days"] or 0) > 0 or (recurring["amount_error_mae"] or 0) > 0


def test_negative_cash_metrics_are_unsupported_without_both_outcomes():
    report = run()
    assert report.negative_cash["supported"] is False
    assert report.negative_cash["precision"] is None and report.negative_cash["recall"] is None


def test_negative_cash_precision_and_recall_when_both_outcomes_exist():
    manual_rule = {
        "rule_id": "manual:rent",
        "account_id": "chk",
        "amount": -500,
        "cadence": "monthly",
        "anchor_date": "2026-06-10",
    }
    poor, rich = date(2026, 6, 1), date(2026, 8, 1)

    def daily(cutoff, start_balance, drop_day):
        out = {}
        for offset in range(0, 31):
            day = cutoff + timedelta(days=offset)
            balance = start_balance - (500 if day.day >= drop_day and day.month == cutoff.month else 0)
            out[offset] = balance
        return out

    snapshots = snaps(poor, daily(poor, 100, 10)) + snaps(rich, daily(rich, 5000, 10))
    loaders = history_loaders(accounts=ACCOUNTS, transactions=[], snapshots=snapshots, manual_rules=[manual_rule])
    report = backtest_v2(cutoffs=[poor, rich], load_inputs=loaders[0], load_truth=loaders[1])
    assert report.negative_cash["supported"] is True
    assert report.negative_cash["precision"] == 1.0 and report.negative_cash["recall"] == 1.0


def test_interval_coverage_is_reported_only_when_uncertainty_is_evaluated():
    assert run().interval_coverage == {}
    report = run(with_uncertainty=True, simulation_count=60, seed=5)
    for key in ("7", "14", "30"):
        entry = report.interval_coverage[key]
        assert entry["samples"] == len(CUTOFFS) and 0 <= entry["coverage"] <= 1 and entry["nominal"] == 0.8


def test_report_is_deterministic_and_json_safe():
    one = json.dumps(run().to_dict(), sort_keys=True)
    two = json.dumps(run().to_dict(), sort_keys=True)
    assert one == two
    data = json.loads(one)
    assert data["model_version"] == "v2" and data["data_window"]["first_cutoff"] == "2026-08-31"


@pytest.mark.parametrize(
    "kwargs,code",
    [
        ({"cutoffs": []}, "no_cutoffs"),
        ({"cutoffs": [date(2026, 1, 1) + timedelta(days=i) for i in range(121)]}, "too_many_cutoffs"),
        ({"horizons": [0]}, "invalid_horizon"),
        ({"horizons": [400]}, "invalid_horizon"),
    ],
)
def test_invalid_backtest_requests_are_rejected(kwargs, code):
    with pytest.raises(ForecastV2InputError) as error:
        run(**kwargs)
    assert error.value.code == code

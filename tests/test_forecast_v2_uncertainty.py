"""Forecast V2 uncertainty: seeded bands, path-based risk and truthful missing-data states."""

import json
import os
import random
import sys
import time
from datetime import date, timedelta
from decimal import Decimal

import pytest

BASE_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BASE_BACKEND not in sys.path:
    sys.path.insert(0, BASE_BACKEND)

from forecast.models import ForecastV2Event  # noqa: E402
from forecast.v2_core import ForecastV2InputError, simulate_cash_ledger  # noqa: E402
from forecast.v2_sources import build_v2_inputs  # noqa: E402
from forecast.v2_uncertainty import estimate_residual_uncertainty, simulate_v2_paths  # noqa: E402

START = date(2026, 11, 2)  # a Monday
ACCOUNTS = [{"account_id": "chk", "type": "depository", "subtype": "checking", "balance": 2000}]


def flat_history(days=35, spend="0.00", start=date(2026, 9, 28)):
    return [{"date": (start + timedelta(days=i)).isoformat(), "spend": spend, "income": "0.00"} for i in range(days)]


def varied_history(days=63, start=date(2026, 8, 31), seed=7):
    rng = random.Random(seed)
    rows = []
    for i in range(days):
        spend = -Decimal(rng.choice([0, 0, 12, 25, 40, 90, 180])).quantize(Decimal("0.01"))
        rows.append({"date": (start + timedelta(days=i)).isoformat(), "spend": str(spend), "income": "0.00"})
    return rows


def manual(day, amount, kind, source="manual", confidence=None, **meta):
    return ForecastV2Event(
        event_id=f"{source}:{kind}:{day}",
        date=date.fromisoformat(day),
        amount=Decimal(str(amount)),
        account_id="chk",
        kind=kind,
        source_id=f"{kind}-{day}",
        source=source,
        confidence=confidence,
        metadata=meta,
    )


def run(**overrides):
    params = dict(
        start_date=START,
        horizon_days=30,
        account_snapshots=ACCOUNTS,
        scheduled_events=[],
        residual_events=[],
        residual_history=varied_history(),
        simulation_count=200,
        seed=1,
        threshold=500,
    )
    params.update(overrides)
    return simulate_v2_paths(**params)


def test_estimate_residual_uncertainty_needs_complete_weeks():
    ok = estimate_residual_uncertainty(varied_history())
    assert ok["available"] and ok["week_count"] == 9 and ok["weekly_net_stdev"] > 0
    short = estimate_residual_uncertainty(flat_history(days=20))
    assert not short["available"] and short["reason"].startswith("insufficient_history")
    assert short["weekly_net_stdev"] is None and short["weeks"] == []


def test_same_seed_is_identical_and_different_seed_changes_bands_not_baseline():
    kwargs = dict(
        scheduled_events=[manual("2026-11-05", -300, "scheduled_bill"), manual("2026-11-20", 900, "scheduled_income")]
    )
    one, two = run(seed=42, **kwargs), run(seed=42, **kwargs)
    other = run(seed=43, **kwargs)
    assert json.dumps(one.to_dict(), sort_keys=True) == json.dumps(two.to_dict(), sort_keys=True)
    assert one.baseline == other.baseline
    assert one.bands != other.bands or one.risk != other.risk
    assert [b["baseline"] for b in one.bands] == [b["baseline"] for b in other.bands]


def test_bands_are_monotonic_and_risk_is_a_probability():
    result = run(scheduled_events=[manual("2026-11-10", -1500, "scheduled_bill")])
    assert result.uncertainty_available and len(result.bands) == 30
    for band in result.bands:
        assert band["p10"] <= band["p50"] <= band["p90"]
    risk = result.risk
    assert 0 <= risk["probability_cash_below_zero_any_day"] <= risk["probability_cash_below_threshold_any_day"] <= 1
    assert risk["simulation_count"] == 200 and risk["seed"] == 1 and risk["model_version"] == "v2"
    assert risk["history_coverage_days"] == 63


def test_risk_comes_from_the_whole_path_not_the_ending_balance():
    # Cash dips to -300 on day 4 in every path, then recovers well above zero.
    result = run(
        account_snapshots=[{**ACCOUNTS[0], "balance": 500}],
        scheduled_events=[manual("2026-11-05", -800, "scheduled_bill"), manual("2026-11-12", 3000, "scheduled_income")],
        residual_history=flat_history(),
    )
    assert result.risk["probability_cash_below_zero_any_day"] == 1.0
    assert result.bands[-1]["p10"] > 0  # the ending balance alone would hide the shortfall
    assert result.risk["probability_cash_below_threshold_any_day"] == 1.0


def test_known_commitments_are_fixed_and_collapse_without_residual_variance():
    result = run(
        scheduled_events=[manual("2026-11-05", -300, "scheduled_bill"), manual("2026-11-20", 900, "scheduled_income")],
        residual_history=flat_history(),
    )
    for band in result.bands:
        assert band["p10"] == band["p50"] == band["p90"] == band["baseline"]
    assert result.assumptions["uncertain_event_count"] == 0 and result.assumptions["fixed_event_count"] == 2


def test_baseline_matches_the_deterministic_ledger_exactly():
    scheduled = [manual("2026-11-05", -300, "scheduled_bill")]
    residual = [manual("2026-11-03", -20, "residual", source="residual")]
    result = run(scheduled_events=scheduled, residual_events=residual)
    ledger = simulate_cash_ledger(
        start_date=START, horizon_days=30, account_snapshots=ACCOUNTS, events=scheduled + residual
    )
    assert [b["baseline"] for b in result.bands] == [float(p.ending_cash) for p in ledger.daily]


def test_varied_residual_spending_is_wider_than_constant_spending():
    constant = run(residual_history=flat_history(days=63, spend="-30.00"))
    varied = run(residual_history=varied_history())
    last = lambda r: r.bands[-1]["p90"] - r.bands[-1]["p10"]  # noqa: E731
    assert last(constant) == 0
    assert last(varied) > 100


def test_inferred_streams_jitter_together_while_manual_ones_do_not():
    uncertain = manual("2026-11-06", 1000, "scheduled_income", source="inferred", confidence=0.6, amount_dispersion=0.1)
    result = run(scheduled_events=[uncertain], residual_history=flat_history(), simulation_count=400)
    day_before, pay_day = result.bands[3], result.bands[4]  # Nov 5 and Nov 6
    assert day_before["p10"] < day_before["p90"]  # some paths pay one day early
    assert pay_day["p10"] < pay_day["p90"]
    assert result.assumptions["uncertain_streams"] == ["scheduled_income-2026-11-06"]


def test_sparse_history_reports_unavailable_instead_of_narrow_bands():
    result = run(residual_history=flat_history(days=10, spend="-5.00"))
    assert result.uncertainty_available is False
    assert "insufficient_history" in result.reason
    assert result.bands == [] and result.risk == {}
    assert len(result.baseline) == 30  # baseline and coverage are still returned
    assert result.history_coverage_days == 10


def test_foreign_only_accounts_yield_no_estimate():
    result = run(account_snapshots=[{**ACCOUNTS[0], "user_id": "other"}], owner_id="me")
    assert result.uncertainty_available is False and result.reason == "no_liquid_cash_accounts"


@pytest.mark.parametrize(
    "overrides,code",
    [
        ({"simulation_count": 1001}, "invalid_simulation_count"),
        ({"simulation_count": 0}, "invalid_simulation_count"),
        ({"horizon_days": 366}, "invalid_horizon"),
        ({"horizon_days": 0}, "invalid_horizon"),
        ({"threshold": -1}, "invalid_threshold"),
        ({"threshold": "nan"}, "invalid_threshold"),
        ({"threshold": "abc"}, "invalid_threshold"),
        ({"seed": "7"}, "invalid_seed"),
        ({"account_snapshots": []}, "empty_account_scope"),
    ],
)
def test_resource_and_input_limits_are_enforced(overrides, code):
    with pytest.raises(ForecastV2InputError) as error:
        run(**overrides)
    assert error.value.code == code


def test_pipeline_end_to_end_and_runtime_budget():
    rng = random.Random(3)
    transactions = []
    for i in range(120):
        day = date(2026, 11, 1) - timedelta(days=i + 1)
        if rng.random() < 0.7:
            transactions.append(
                {
                    "transaction_id": f"t{i}",
                    "account_id": "chk",
                    "date": day.isoformat(),
                    "amount": -rng.choice([8, 14, 33, 61, 120]),
                    "name": f"Shop{chr(65 + i % 26)}",
                }
            )
    inputs = build_v2_inputs(
        transactions=transactions,
        accounts=ACCOUNTS,
        as_of_date="2026-11-01",
        start_date=START,
        horizon_days=365,
    )
    started = time.perf_counter()
    result = simulate_v2_paths(
        start_date=START,
        horizon_days=365,
        account_snapshots=ACCOUNTS,
        scheduled_events=inputs["scheduled_events"],
        residual_events=inputs["residual_events"],
        residual_history=inputs["residual_history"],
        simulation_count=1000,
        seed=9,
        threshold=250,
    )
    elapsed = time.perf_counter() - started
    assert result.uncertainty_available and len(result.bands) == 365
    assert elapsed < 20, f"1000x365 simulation took {elapsed:.1f}s"

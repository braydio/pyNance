"""Forecast V2 service: scoping, liquidity semantics, uncertainty and scenarios."""

import os
import sys
from datetime import date, timedelta
from decimal import ROUND_HALF_EVEN, Decimal

os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
sys.path.insert(0, os.path.dirname(__file__))

import pytest
from app.extensions import db
from app.services.forecast_v2_service import (
    ForecastV2AccessError,
    ForecastV2RequestError,
    compute_v2_forecast,
)
from flask import Flask
from forecast_v2_world import START, seed_world

TODAY = date(2026, 10, 14)


@pytest.fixture()
def database():
    app = Flask(__name__)
    app.config.update(SQLALCHEMY_DATABASE_URI="sqlite:///:memory:", SQLALCHEMY_TRACK_MODIFICATIONS=False)
    db.init_app(app)
    with app.app_context():
        db.create_all()
        seed_world()
        yield app
        db.session.remove()
        db.drop_all()


def compute(**overrides):
    payload = {"user_id": "alice", "start_date": START.isoformat(), "horizon_days": 60, **overrides}
    return compute_v2_forecast(payload, today=TODAY)


def test_liquid_cash_is_separate_from_debt_investments_and_net_worth(database):
    result = compute()
    assert result["model_version"] == "v2" and result["status"] == "ok"
    assert result["liquidity"]["starting_cash"] == 5000.0  # checking + savings only
    assert result["net_worth"]["liabilities"]["starting"] == 700.0
    assert result["net_worth"]["investments"]["starting"] == 5000.0
    assert result["net_worth"]["starting"] == 5000.0 + 5000.0 - 700.0
    assert result["metadata"]["balance_basis"] == "liquid_cash"
    assert result["timeline"][0]["forecast_balance"] == result["timeline"][0]["liquid_cash"]
    buckets = result["metadata"]["account_buckets"]
    assert buckets["cash"] == ["chk", "sav"] and buckets["liability"] == ["card"]


def test_summary_reconciles_to_timeline_and_events(database):
    result = compute()
    summary, timeline = result["summary"], result["timeline"]
    assert len(timeline) == 60
    assert timeline[-1]["liquid_cash"] == summary["ending_balance"]
    assert round(summary["starting_balance"] + summary["total_inflows"] - summary["total_outflows"], 2) == round(
        summary["ending_balance"], 2
    )
    assert result["series"]["debt_totals"]["points"][0]["value"] == 700.0


def test_rent_and_paychecks_appear_once_and_are_not_in_the_residual(database):
    result = compute()
    drivers = result["drivers"]
    rent = [d for d in drivers if d["kind"] == "scheduled_bill" and d["amount"] == -1500.0]
    pay = [d for d in drivers if d["kind"] == "scheduled_income" and d["amount"] == 2000.0]
    assert [d["date"] for d in rent] == ["2026-11-01", "2026-12-01"]
    assert len(pay) >= 4 and len({d["date"] for d in pay}) == len(pay)
    assert all(d["origin"] == "detected_recurring" for d in rent + pay)
    residual_outflow = -sum(c["amount"] for c in result["cashflows"] if c["category"] == "residual" and c["amount"] < 0)
    assert residual_outflow < 60 * 150  # a few thousand, not rent-sized daily noise


@pytest.mark.parametrize("horizon", [1, 7, 30, 90])
def test_horizons_return_exact_day_counts(database, horizon):
    result = compute(horizon_days=horizon)
    assert len(result["timeline"]) == horizon
    assert result["timeline"][0]["date"] == START.isoformat()
    assert result["summary"]["end_date"] == (START + timedelta(days=horizon - 1)).isoformat()


def test_only_the_users_accounts_are_used_and_foreign_ids_fail_closed(database):
    result = compute()
    assert "bob-chk" not in result["metadata"]["account_buckets"]["cash"]
    with pytest.raises(ForecastV2AccessError):
        compute(included_account_ids=["chk", "bob-chk"])
    with pytest.raises(ForecastV2AccessError):
        compute(included_account_ids=["does-not-exist"])
    narrowed = compute(included_account_ids=["chk"])
    assert narrowed["liquidity"]["starting_cash"] == 4000.0


@pytest.mark.parametrize(
    "overrides",
    [
        {"horizon_days": 0},
        {"horizon_days": 366},
        {"horizon_days": "30"},
        {"start_date": "tomorrow"},
        {"start_date": "2030-01-01"},
        {"user_id": ""},
        {"simulation": {"enabled": True, "count": 1001}},
        {"simulation": {"enabled": True, "cash_threshold": -5}},
        {"simulation": "yes"},
        {"scenarios": [{"id": f"s{i}", "changes": {}} for i in range(6)]},
        {"scenarios": [{"id": "x", "changes": {"teleport_money": 1}}]},
        {"scenarios": [{"id": "x", "changes": {"residual_spending_multiplier": 9}}]},
        {"scenarios": [{"id": "x", "changes": {"delay_income_days": 90}}]},
        {"scenarios": [{"id": "x", "changes": {}}, {"id": "x", "changes": {}}]},
        {"scenarios": [{"id": "baseline", "changes": {"income_multiplier": 2}}]},
        {"adjustments": "nope"},
    ],
)
def test_invalid_requests_raise_request_errors(database, overrides):
    with pytest.raises(ForecastV2RequestError):
        compute(**overrides)


def test_bad_adjustment_content_is_a_request_error(database):
    with pytest.raises(ForecastV2RequestError):
        compute(adjustments=[{"amount": "lots", "date": "2026-11-05"}])


def test_manual_adjustments_apply_once_and_move_cash_exactly(database):
    base = compute()
    adjusted = compute(adjustments=[{"adjustment_id": "gift", "amount": -250, "date": "2026-11-10", "label": "Gift"}])
    assert round(adjusted["liquidity"]["ending_cash"] - base["liquidity"]["ending_cash"], 2) == -250.0
    assert adjusted["series"]["manual_adjustments"]["points"][9]["value"] == -250.0
    assert adjusted["adjustments"][0]["label"] == "Gift"


def test_uncertainty_is_off_by_default_and_never_fabricated(database):
    off = compute()
    assert off["uncertainty"] == {"available": False, "reason": "simulation_disabled"}
    assert "p10" not in off["timeline"][0]


def test_simulation_adds_ordered_bands_risk_and_is_seed_stable(database):
    sim = {"enabled": True, "count": 200, "seed": 7, "cash_threshold": 100000}
    one, two = compute(simulation=sim), compute(simulation=sim)
    assert one["uncertainty"]["available"] is True
    assert one["timeline"] == two["timeline"] and one["uncertainty"] == two["uncertainty"]
    for row in one["timeline"]:
        assert row["p10"] <= row["p50"] <= row["p90"]
    assert one["uncertainty"]["risk_below_threshold_any_day"] == 1.0  # threshold far above any balance
    assert 0 <= one["uncertainty"]["risk_below_zero_any_day"] <= 1
    assert one["uncertainty"]["sample_count"] == 200 and one["uncertainty"]["seed"] == 7
    other = compute(simulation={**sim, "seed": 8})
    assert [r["liquid_cash"] for r in other["timeline"]] == [
        r["liquid_cash"] for r in one["timeline"]
    ]  # baseline fixed
    assert [(r["p10"], r["p90"]) for r in other["timeline"]] != [(r["p10"], r["p90"]) for r in one["timeline"]]


def test_low_cash_probability_responds_to_a_large_known_bill(database):
    risky = compute(
        simulation={"enabled": True, "count": 200, "seed": 3},
        adjustments=[{"adjustment_id": "tax", "amount": -9000, "date": "2026-11-05"}],
    )
    assert risky["uncertainty"]["risk_below_zero_any_day"] > 0.5
    assert risky["liquidity"]["first_shortfall_date"] is not None


def income_events(result):
    return [c for c in result["cashflows"] if c["category"] == "scheduled_income"]


def test_delayed_paycheck_scenario_changes_ending_cash_only_by_pushed_out_income(database):
    result = compute(
        horizon_days=30,
        scenarios=[{"id": "late", "label": "Paycheck 7 days late", "changes": {"delay_income_days": 7}}],
    )
    assert [s["id"] for s in result["scenarios"]] == ["baseline", "late"]
    base, late = result["scenarios"]
    assert base["delta_vs_baseline"] == {"ending_cash": 0.0, "min_cash": 0.0}
    end = date.fromisoformat(result["summary"]["end_date"])
    pushed = sum(c["amount"] for c in income_events(result) if date.fromisoformat(c["date"]) + timedelta(days=7) > end)
    assert pushed > 0
    assert late["delta_vs_baseline"]["ending_cash"] == -round(pushed, 2)
    assert late["min_cash"] <= base["min_cash"]


def test_spending_cut_scenario_changes_only_residual_spending(database):
    result = compute(
        horizon_days=30,
        scenarios=[{"id": "cut", "label": "Spending down 15%", "changes": {"residual_spending_multiplier": 0.85}}],
    )
    spend = [Decimal(str(c["amount"])) for c in result["cashflows"] if c["category"] == "residual" and c["amount"] < 0]
    expected = sum(-a for a in spend) - sum(
        (-a * Decimal("0.85")).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN) for a in spend
    )
    cut = result["scenarios"][1]
    assert Decimal(str(cut["delta_vs_baseline"]["ending_cash"])) == expected
    assert cut["delta_vs_baseline"]["ending_cash"] > 0


def test_scenario_adjustments_and_income_multiplier_replay_through_the_engine(database):
    result = compute(
        horizon_days=30,
        scenarios=[
            {
                "id": "bonus",
                "changes": {"adjustments": [{"adjustment_id": "bonus", "amount": 500, "date": "2026-11-05"}]},
            },
            {"id": "raise", "changes": {"income_multiplier": 1.5}},
        ],
    )
    _, bonus, raise_ = result["scenarios"]
    assert bonus["delta_vs_baseline"]["ending_cash"] == 500.0
    in_window = sum(c["amount"] for c in income_events(result))
    assert raise_["delta_vs_baseline"]["ending_cash"] == round(in_window * 0.5, 2)
    assert [p["date"] for p in bonus["timeline"]] == [t["date"] for t in result["timeline"]]


def test_probabilistic_scenario_deltas_use_shared_random_draws(database):
    sim = {"enabled": True, "count": 150, "seed": 21, "cash_threshold": 2000}
    result = compute(horizon_days=30, simulation=sim, scenarios=[{"id": "same", "changes": {}}])
    base, same = result["scenarios"]
    assert same["risk"]["delta_vs_baseline"] == {
        "probability_cash_below_zero_any_day": 0.0,
        "probability_cash_below_threshold_any_day": 0.0,
    }
    worse = compute(
        horizon_days=30,
        simulation=sim,
        scenarios=[{"id": "worse", "changes": {"residual_spending_multiplier": 1.5}}],
    )["scenarios"][1]
    assert worse["risk"]["delta_vs_baseline"]["probability_cash_below_threshold_any_day"] >= 0


def test_no_liquid_cash_degrades_transparently(database):
    result = compute(included_account_ids=["card"])
    assert result["status"] == "insufficient_data" and result["timeline"] == []
    assert result["uncertainty"]["available"] is False
    assert any(w["code"] == "no_liquid_cash_accounts" for w in result["data_quality"]["warnings"])


def test_past_start_never_anchors_to_todays_balance(database):
    result = compute(start_date="2026-09-01")  # no snapshots on/before 2026-08-31
    assert result["status"] == "insufficient_data"
    assert not any(w["code"] == "anchored_to_current_balance" for w in result["data_quality"]["warnings"])


def test_future_start_without_a_snapshot_uses_current_balance_with_a_warning(database):
    from app.models import Account, AccountHistory

    AccountHistory.query.filter(AccountHistory.account_id == "chk").delete()
    Account.query.filter_by(account_id="chk").update({"balance": Decimal("1234.00")})
    db.session.commit()
    result = compute_v2_forecast(
        {"user_id": "alice", "start_date": "2026-10-20", "horizon_days": 5, "included_account_ids": ["chk"]},
        today=date(2026, 10, 14),
    )
    assert result["liquidity"]["starting_cash"] == 1234.0
    assert any(w["code"] == "anchored_to_current_balance" for w in result["data_quality"]["warnings"])

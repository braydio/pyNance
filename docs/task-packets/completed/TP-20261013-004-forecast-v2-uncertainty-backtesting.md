# TP-20261013-004: Forecast V2 Probabilities + Rolling Backtesting

**Packet ID:** TP-20261013-004  
**Status:** Complete  
**Created:** 2026-10-13  
**Last updated:** 2026-10-13  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/completed/TP-20261013-004-forecast-v2-uncertainty-backtesting.md`  
**Workstream size:** One implementation packet  
**Depends on:** TP-20261013-003  
**Priority:** Normal  
**Series:** Forecast V2, packet 3 of 4 (execute 002 -> 003 -> 004 -> 005)  


## Objective

Measure reliability of the V2 event-driven cash forecast with **rolling historical backtests**, then generate bounded, seeded uncertainty simulations with **P10/P50/P90 daily liquid-cash balances**, horizon shortfall risks, and transparent confidence/data-coverage explanations. Probability output must be evidence-based and clearly distinguished from deterministic baseline and heuristic source confidence.

## Confirmed implementation surface

- `backend/forecast/v2_core.py`, `backend/forecast/models.py` from TP-20261013-002; `backend/forecast/v2_sources.py` and `backend/app/services/forecast_v2_sources.py` from TP-20261013-003.
- `backend/forecast/engine.py::compute_summary` / `compute_forecast` are current deterministic V1 projection/summary functions. Retain backward compatibility.
- `backend/app/models/account_models.py::AccountHistory` holds dated per-account snapshots. `backend/app/models/transaction_models.py::Transaction` supplies dated booked events.
- `backend/app/services/forecast_stat_model.py::ForecastEngine.evaluate` currently computes ARIMA MSE on a held-out numeric series. **This is not a leakage-safe daily-cash forecast backtest**, and ARIMA need not be a dependency for V2.

## Quantitative contract

**New pure module:** `backend/forecast/v2_validation.py`; **new optional uncertainty module:** `backend/forecast/v2_uncertainty.py`. Extend V2 typed models with `ForecastBacktestReport` and `ForecastUncertaintyResult` (names may be equally descriptive).

Daily bounds:
```json
{"date":"2026-11-01","p10":650.25,"p50":1310.00,"p90":1850.75,"baseline":1360.00}
```
**P10** is the 10th percentile of *liquid cash balance* and **P90** the 90th; enforce P10<=P50<=P90. A lower percentile means less cash, not more. Keep baseline deterministic and independent; P50 median need **not** equal baseline. Nonnegative calibration/coverage display must never imply guarantee.

Risk:
```json
{
 "probability_cash_below_zero_any_day":0.18,
 "probability_cash_below_threshold_any_day":0.28,
 "threshold":500.00,
 "simulation_count":500,
 "seed":12345,
 "model_version":"v2",
 "history_coverage_days":90
}
```
Each simulated path must use the exact same starting liquid cash and known contractual events as the deterministic baseline, then vary **only uncertain inputs** (residual variable spend, date jitter on explicitly uncertain inferred events, amount variance with documented limits). Deterministic confirmed bills, user overrides and known transactions are fixed unless the user explicitly provides a range. Preserve source-level correlation within a stream and avoid sampling unbounded independent noise every day. Seeded RNG local to the simulation call, no process-global randomness; stable input order and deterministic serialization. Cap default simulation_count (e.g. 500), maximum 1000, horizon max 365 and reject invalid resource requests.

**No fake confidence:** If insufficient clean historical days/observations for variance estimation, return `uncertainty_available:false` with reason, deterministic baseline and model coverage. Do not manufacture narrow percentile intervals. Distinguish numeric simulation risk, heuristic detection confidence and empirical interval coverage.

Backtesting: for each supported cutoff `as_of_date`, build V2 inputs **only from <= cutoff data**, replay 7-, 14- and 30-day horizons, compare end-of-day *liquid-cash* predictions against realized eligible cash-account snapshots/validated actual ledger. Prefer historical snapshots; only reconstruct actuals from transaction movement where anchor and completeness are evidenced. Do not use today's balance at historical cutoffs. Skip unknown/missing truth windows and report evaluated/skipped counts, never treat missing as zero. Metrics:
- Balance MAE and signed bias by horizon; sample count.
- Recurring next-occurrence date error (days), amount error (dollars).
- Negative-cash-event precision/recall if **both** event classes have evidence; otherwise null/unsupported, not manufactured 100%.
- P10/P90 empirical inclusion coverage when probabilistic forecasts exist.
- Version, data window, coverage and rationale for excluded folds.

## Required work / order

1. Implement reusable `backtest_v2(as_of_dates, load_snapshot, load_transactions, ...)` orchestration using Packet 003 as-of loaders; ensure rolling train/test boundaries and no leakage.
2. Implement `estimate_residual_uncertainty` from clean historic residuals: robust per-category/weekday variance with fallback only when justified by sample count; document assumptions.
3. Implement `simulate_v2_paths` using Packet 002 ledger and seeded draws; calculate percentiles and cash threshold/negative risks from per-path daily minima.
4. If sample too small, return insufficient-data status without bands. Provide resource limits, performance tests, and provenance metadata.
5. Documentation `docs/backend/forecast/v2_validation.md`, `docs/backend/forecast/v2_uncertainty.md`. Do not add new API endpoints yet.

## Tests

New `tests/test_forecast_v2_validation.py`, `tests/test_forecast_v2_uncertainty.py`; rely on established `test_forecast_v2_core.py` and `test_forecast_v2_sources.py`.

- **Leakage trap:** after the simulated as-of date, mutate future transactions and current snapshots; every corresponding backtest forecast stays unchanged.
- Backtest cutoffs with known cash history: correctly compute 7/14/30-day MAE and signed error; skip missing holdout truth and report count.
- Perfect regular payroll/rent case: next-occurrence timing and amount error zero; irregular cases return nonzero measured errors.
- Same inputs/seed produce identical P10/P50/P90 and risk; changing seed changes stochastic values but keeps confirmed-event baseline.
- Percentiles monotonic, risk in [0,1], risk computed from whole simulated **path** rather than end balance.
- Synthetic varied residual spending produces wider dispersion than fully deterministic case. Sparse data omits uncertainty instead of reporting certainty.
- Reject huge simulation count/horizon, invalid numeric thresholds, empty/unauthorized account scope.
- Full suite remains green; no changes to existing V1 calculations.

Commands:
```bash
pytest tests/test_forecast_v2_validation.py tests/test_forecast_v2_uncertainty.py tests/test_forecast_v2_core.py tests/test_forecast_v2_sources.py -q
pytest -q
python scripts/check_docs.py --changed-since origin/main
```

## Acceptance criteria

- [ ] Historical as-of backtests are reproducible, correctly scored at 7/14/30 days, and demonstrably leakage-safe.
- [ ] Seeded Monte Carlo provides per-day P10/P50/P90 and well-defined negative-cash/threshold probabilities.
- [ ] Known commitments remain deterministic; stochastic variability only where justified by evidence.
- [ ] Uncertainty missing-data states are truthful; coverage/evaluation sample size exposed.
- [ ] Bounds, runtime budget and tests are enforced.
- [ ] Existing V1 forecast remains unaffected.

## Non-goals

No chart UI, production default switch, unvalidated risk claims, heavy ARIMA/ML training, auto-trading, investment price forecasts, credit underwriting, or unsolicited debt amortization modeling.

## Handoff / dependencies

Next: TP-20261013-005 adds versioned endpoint/frontend and scenario comparison using these return contracts. No need to replace V1 or invent a second orchestration framework.

## Completion report

`Workstream: TP-20261013-004`, status, commit URL, metrics and synthetic validation fixture, test commands/results, performance/safety bounds, known limitations, next packet.

## Execution rules (AGENTS.md)

Implement from this canonical packet, not old docs. Check the packet tracker and only the listed symbols against latest `main`; mark packet and tracker `In Progress` when starting. On completion, run tests, set `Complete`, move the packet to `completed/`, and update INDEX/TRACKER in the same commit. Keep local/origin `main` synchronized without force-push and report exact tests, deviations, blockers, and commit URL. Do not fabricate the authoring chat URL.


---

## Completion report (2026-10-13)

Workstream: TP-20261013-004
Status: Complete

**Delivered**
- `backend/forecast/v2_validation.py`: `backtest_v2` (rolling as-of replay at 7/14/30 days) and `history_loaders` (as-of slicing of in-memory history).
- `backend/forecast/v2_uncertainty.py`: `estimate_residual_uncertainty` and `simulate_v2_paths` (seeded Monte Carlo, P10/P50/P90 liquid-cash bands, path-minimum shortfall risk).
- `backend/forecast/models.py`: additive `ForecastBacktestReport`, `ForecastUncertaintyResult`.
- `backend/forecast/v2_sources.py`: now also returns `residual_history` (complete daily residual grid) and per-stream `amount_dispersion`; sources behavior otherwise unchanged.
- Docs: `docs/backend/forecast/v2_validation.md`, `v2_uncertainty.md`, sources doc and roadmap updated. No API endpoint added; V1 untouched.

**Method and contracts**
- Uncertain inputs: inferred streams (one shared date shift of -1/0/+1 day with odds `1 - detection confidence`, one shared amount factor within observed dispersion, per path) and residual spend/income (block bootstrap by calendar week from the user's own history, never exceeding observed values). Manual rules, saved rules and adjustments are fixed; every path starts from the baseline's cash.
- Risk uses each path's minimum balance over the horizon. Missing history (<4 complete weeks) returns `uncertainty_available: false` with a reason and baseline only. Limits: 1..1000 simulations, horizon 1..365, finite non-negative threshold, integer seed, non-empty account scope; 120 cutoffs per backtest.
- Backtest metrics: MAE and signed bias (predicted - actual) per horizon, recurring date/amount error with matched/missed/unobserved counts, negative-cash precision/recall only when both outcomes exist, P10-P90 empirical coverage when requested, skipped-fold counts by reason (missing truth is never zero).

**Synthetic validation fixture (tests):** one checking account over 10 months with biweekly payroll, monthly rent and fixed weekday spend; cutoffs every 7 days from 2026-08-31. The regular world scores MAE 0.0 / bias 0.0 and zero recurring date and amount error (35 matched streams); the jittered-payroll variant measures nonzero date (0.0857 days) and amount ($11.43) error and balance MAE of $20-$80.

**Verification (commands run)**
- `.venv/bin/python -m pytest tests/test_forecast_v2_validation.py tests/test_forecast_v2_uncertainty.py tests/test_forecast_v2_core.py tests/test_forecast_v2_sources.py tests/test_forecast_v2_adapters.py tests/test_forecast_engine.py -q` -> 129 passed. Leakage trap: mutating all transactions and snapshots after the cutoff leaves predictions identical. Runtime: 1000 paths x 365 days well under 1 s.
- Full `pytest -q` still cannot collect (pre-existing); per-file runs show only the same pre-existing failures as a clean checkout. `black`/`ruff` clean.

**Known limitations:** truth comes from recorded snapshots only (no reconstruction from transactions); empirical coverage on a short or perfectly regular history is not informative (the regular fixture covers 100%); bootstrap bands assume the past week-to-week variability repeats; no category-level variance.

**Next packet:** TP-20261013-005 (V2 API, scenarios, frontend integration).

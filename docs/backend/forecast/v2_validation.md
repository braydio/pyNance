---
Owner: Backend Team
Last Updated: 2026-10-14
Status: Active
---

# Forecast V2 Validation (Rolling Backtests)

## Purpose

`backend/forecast/v2_validation.py` measures how well the V2 forecast would have done, using only data
available at each historical cutoff. It is pure; data comes through loader callables. It replaces nothing
in V1 and is not the ARIMA MSE helper in `forecast_stat_model.py` (a held-out numeric series, not a
leakage-safe cash backtest).

## Interface

```python
backtest_v2(cutoffs, load_inputs, load_truth, load_realized=None, horizons=(7, 14, 30),
            max_anchor_age_days=1, recurring_match_days=5, with_uncertainty=False,
            simulation_count=200, seed=12345, options=None) -> ForecastBacktestReport
history_loaders(accounts, transactions, snapshots, recurring_rules=(), manual_rules=())
    -> (load_inputs, load_truth, load_realized)
```

Per cutoff `c`, the pipeline runs `v2_sources.build_v2_inputs(as_of_date=c, start=c+1)` and
`simulate_cash_ledger` over the longest horizon, then scores the end-of-day cash at each horizon.

## No leakage

- `load_inputs(c)` supplies each account's balance from the latest snapshot **on or before** `c`; the
  sources pipeline additionally rejects any transaction dated after `c`. Today's balance is never used.
- A fold needs a cash-account anchor no older than `max_anchor_age_days`; otherwise it is skipped
  (`stale_anchor` / `no_anchor_snapshot`).
- Each fold record keeps its predictions separately from the truth, so tests can mutate everything after the
  cutoff and verify that predictions do not move.

## Metrics

| Metric | Definition |
| --- | --- |
| `balance[h]` | `samples`, `mae`, signed `bias` = predicted - actual (positive = over-forecast) for end-of-day liquid cash. Truth is the sum of eligible cash snapshots on that exact day and is unknown unless every cash account has one. |
| `recurring` | For each promoted non-manual stream, first projected occurrence vs the nearest realized transaction of the same account/merchant/sign within `recurring_match_days`: `date_error_*_days`, `amount_error_mae`, plus `matched`, `missed` and `unobserved` (predicted date beyond observed data). |
| `negative_cash` | Precision/recall of "cash goes negative within the longest horizon". `supported: false` and null values unless evaluated folds include both outcomes. |
| `interval_coverage[h]` | Share of horizons where actual cash fell inside simulated P10-P90 (nominal 0.8). Only with `with_uncertainty=True`. |
| `skipped` | Counts by reason: `stale_anchor`, `no_anchor_snapshot`, `insufficient_data`, `no_truth_in_window`, and `missing_truth_horizons` (individual horizon samples). Missing truth is never counted as zero. |

`data_window` and each fold's `history_days` / `coverage_confidence` expose how much evidence backed a fold.

## Limits

Up to 120 cutoffs and horizons 1..365 per call (`ForecastV2InputError` otherwise). Truth uses recorded
account snapshots only; reconstructing actuals from transactions is intentionally not done here.

## Tests

`tests/test_forecast_v2_validation.py` (leakage trap, exact MAE/bias, skipped folds, recurring error,
negative-cash support rule, coverage, determinism).

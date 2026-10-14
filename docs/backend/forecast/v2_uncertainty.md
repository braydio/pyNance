---
Owner: Backend Team
Last Updated: 2026-10-14
Status: Active
---

# Forecast V2 Uncertainty (Seeded Monte Carlo)

## Purpose

`backend/forecast/v2_uncertainty.py` puts evidence-based bands and shortfall risk around the
deterministic V2 baseline (`docs/backend/forecast/v2_core.md`). It does not replace the baseline and adds
no API endpoint. Result type: `ForecastUncertaintyResult` in `backend/forecast/models.py`.

## Interface

```python
simulate_v2_paths(start_date, horizon_days, account_snapshots, scheduled_events,
                  residual_events=(), residual_history=(), simulation_count=500,
                  seed=<int, required>, threshold=0, owner_id=None) -> ForecastUncertaintyResult
estimate_residual_uncertainty(residual_history, min_weeks=4) -> dict
```

`scheduled_events`, `residual_events` and `residual_history` come from `v2_sources.build_v2_inputs`.

## What varies, and what does not

Every path starts from the same liquid cash and the same known events as the baseline.

| Input | Treatment |
| --- | --- |
| Manual rules, saved recurring rules, adjustments | Fixed |
| Inferred recurring streams (`source == "inferred"`) | One date shift (-1/0/+1 day; total shift odds = `1 - detection confidence`, capped at 50%) and one amount factor (within the stream's observed `amount_dispersion`, max +/-25%) **per path**, shared by every instance of that stream |
| Residual spending/income | Block bootstrap by calendar week from the user's own de-recurred history (Monday-Sunday weeks, aligned by weekday). Values never exceed what was observed |

The baseline residual (winsorized weekday means) and the bootstrap mean differ, so P50 need not equal the
baseline. Randomness is a call-local `random.Random(seed)`; the same inputs and seed give identical output.

## Output

- `bands`: per day `{date, p10, p50, p90, baseline}` of **liquid cash** (lower percentile = less cash;
  `p10 <= p50 <= p90`).
- `risk`: `probability_cash_below_zero_any_day`, `probability_cash_below_threshold_any_day`, `threshold`,
  `simulation_count`, `seed`, `model_version`, `history_coverage_days`. Both probabilities use each path's
  **minimum** balance over the horizon, so a mid-horizon dip counts even if the path recovers.
- `assumptions`: method, history weeks, weekly net mean/stdev, fixed vs uncertain event counts, interval.

## Truthfulness and limits

- Fewer than 4 complete weeks of clean residual history -> `uncertainty_available: false` with a reason,
  baseline only, **no** bands or risk. No fallback narrow interval is manufactured.
- With no usable liquid-cash account (for example only another user's accounts) -> unavailable,
  `no_liquid_cash_accounts`. An empty account list raises `empty_account_scope`.
- Limits: `simulation_count` 1..1000 (default 500), `horizon_days` 1..365, `threshold` a finite
  non-negative number, integer `seed`. Violations raise `ForecastV2InputError` with a stable `code`.
  1000 paths over 365 days runs well under a second in tests.
- Three different things are never mixed: the deterministic baseline, the heuristic stream detection
  confidence from `v2_sources`, and simulation percentiles. Percentiles reflect limited history and are not
  guarantees; validate them with `docs/backend/forecast/v2_validation.md` (empirical P10-P90 coverage).

## Tests

`tests/test_forecast_v2_uncertainty.py`.

---
Owner: Backend Team
Last Updated: 2026-01-25
Status: Active
---

# Forecast Engine Helpers

## Purpose

`backend/forecast/engine.py` contains the deterministic, rule-based projection helpers used to
assemble forecast timelines. The functions operate on pre-aggregated balance snapshots and
historical inflow/outflow aggregates, returning `ForecastTimelinePoint` entries for downstream API
responses and composing serialized payloads when needed.

## `project_balances`

`project_balances(user_id, start_date, horizon_days, latest_snapshots, historical_aggregates)`
creates a daily timeline beginning at `start_date`, anchoring the forecast at the latest known
balances for the user, and applying average daily inflows/outflows derived from historical
aggregates.

### Inputs

- **user_id**: The user identifier for filtering snapshot data.
- **start_date**: The first date in the forecast window (string, `date`, or `datetime`).
- **horizon_days**: Number of days to project, including the start date.
- **latest_snapshots**: A sequence of mappings that include `balance`, plus optional `account_id`,
  `date`, and `user_id` fields.
- **historical_aggregates**: A sequence of mappings that include `date` and inflow/outflow fields
  such as `inflow`/`outflow` or `income`/`expense`.

### Behavior

- Picks the latest snapshot per account (by date) for the specified user.
- Calculates average daily inflow/outflow from historical aggregates.
- Applies the daily net change to build `ForecastTimelinePoint` entries for each day in the
  horizon.
- Produces deterministic output for identical input sequences.

### Example

```python
from datetime import date
from forecast.engine import project_balances

timeline = project_balances(
    user_id=11,
    start_date=date(2024, 1, 6),
    horizon_days=3,
    latest_snapshots=[{"account_id": "acct-1", "balance": 150.0, "date": "2024-01-05"}],
    historical_aggregates=[{"date": "2023-12-31", "inflow": 80.0, "outflow": 20.0}],
)
```

## `build_cashflow_items`

`build_cashflow_items(timeline, category_averages=None, recurring_sources=None, adjustments=None)`
generates :class:`ForecastCashflowItem` entries for each daily balance delta and optional
adjustments.

### Inputs

- **timeline**: Baseline `ForecastTimelinePoint` sequence used for delta calculations.
- **category_averages**: Optional mappings with category labels and average amounts to attribute
  daily deltas.
- **recurring_sources**: Optional mappings with merchant labels and amounts (plus optional
  frequencies) for recurring cashflows.
- **adjustments**: Optional adjustment entries that should appear in the cashflow breakdown.

### Behavior

- Computes daily deltas from the baseline timeline without mutating it.
- Allocates deltas to recurring sources first, then scales category averages to match the remaining
  delta.
- Adds an `Uncategorized` fallback item when the delta cannot be fully attributed.
- Emits adjustment cashflow items so adjustment impacts appear in breakdowns.

## `apply_adjustments`

`apply_adjustments(baseline_timeline, adjustments)` overlays one-time or recurring adjustments onto
the baseline projection.

### Behavior

- Supports daily, weekly, and monthly adjustment frequencies.
- Applies each adjustment on its effective date and carries the impact forward through the horizon.
- Returns a new list of timeline points without mutating the baseline inputs.

## `compute_summary`

`compute_summary(timeline)` aggregates a timeline into `ForecastSummary` metrics, including starting
and ending balances, net change, min/max balances, and the depletion date (first date where the
projected balance is at or below zero).

## `compute_forecast`

`compute_forecast(...)` orchestrates the forecast pipeline by:

- Loading snapshot and historical aggregate inputs.
- Building a baseline projection with `project_balances`.
- Applying adjustments with `apply_adjustments`.
- Generating cashflow breakdowns and summary metrics.
- Returning a fully serialized `ForecastResult` payload for the API layer.

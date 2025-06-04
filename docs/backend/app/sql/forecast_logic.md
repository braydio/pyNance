# backend/app/sql Documentation

---

## 📘 `forecast_logic.py`

```markdown
# Forecast Logic Module

## Purpose

Implements the SQL-backed logic for generating financial forecasts, including both balance projections and statistical trend extrapolations. Acts as a low-level interface for reading and preparing data used in forecast models.

## Key Responsibilities

- Aggregate historical transaction data
- Prepare inputs for model-based forecasting
- Join balances, categories, and time series into unified views

## Primary Functions

- `get_spending_baseline(user_id, category_id, window)`

  - Returns average historical spending over a defined time window

- `get_balance_snapshots(user_id, start_date, end_date)`

  - Returns daily or monthly snapshots of account balances

- `projected_spending_series(user_id)`
  - Assembles data frame ready for input to forecast engine

## Inputs

- `user_id`, `category_id`, `account_ids`
- Time ranges: start and end dates

## Outputs

- Time series of spending and balance data
- Flattened results for forecasting model inputs

## Internal Dependencies

- SQL views, calendar utility tables
- `models.Transaction`, `models.Account`
- `sqlalchemy`, time-series helpers

## Known Behaviors

- Backfills empty months with zero-values to ensure continuity
- Uses calendar join to ensure all time intervals present
- Supports percentile-based trimming to remove outliers

## Related Docs

- [`docs/dataflow/forecast_data_input.md`](../../dataflow/forecast_data_input.md)
- [`docs/models/Forecast.md`](../../models/Forecast.md)
```

---

Ready for `manual_import_logic.py`?

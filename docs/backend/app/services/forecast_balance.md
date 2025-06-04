# backend/app/services Documentation

---

## 📘 `forecast_balance.py`

```markdown
# Forecast Balance Service

## Purpose

Provides logic to calculate and project future account balances based on scheduled recurring transactions and user-configurable inputs. Typically consumed by forecast dashboards and financial planning tools.

## Key Responsibilities

- Generate a forward-looking balance graph
- Simulate account cash flow day-by-day
- Integrate recurring transactions into forecast
- Support configurable lookahead window and smoothing

## Primary Functions

- `generate_balance_projection(start_date, end_date, account_id)`

  - Returns: Daily balance values over the forecast window

- `simulate_cash_flow(account_id, recurring_events, initial_balance)`
  - Core computation for forward balance

## Inputs

- User-selected `start_date`, `end_date`
- `account_id` to focus projection
- Historical transaction trends (read-only)
- Known recurring transactions from database

## Outputs

- Time-series of date → balance
- Optional flags for negative balance days, projected overdraft, etc.

## Internal Dependencies

- `models.RecurringTransaction`
- `services.recurring_detection`
- `datetime`, `pandas` or equivalent time math libs

## Known Behaviors

- Assumes static recurring amounts unless pattern fluctuates
- Applies weekend/holiday shifting if configured
- Can be memoized for identical inputs (cacheable)

## Related Docs

- [`docs/dataflow/forecast_balance_pipeline.md`](../../dataflow/forecast_balance_pipeline.md)
- [`docs/frontend/components/BalanceForecastGraph.md`](../../frontend/components/BalanceForecastGraph.md)
```

---

Next: `forecast_engine.py`?

# backend/app/services Documentation

---

## 📘 `forecast_orchestrator.py`

````markdown
# Forecast Orchestrator Service

## Purpose

High-level coordinator that manages the sequencing and integration of forecast components. It pulls together balance forecasting, statistical projections, and recurring analysis into a unified output. Used as the backend entry point for `/forecast` routes.

## Key Responsibilities

- Compose results from sub-forecast modules
- Validate input parameters and scope
- Manage fallback behavior and defaults
- Return API-consumable forecast payload

## Primary Functions

- `build_forecast_payload(user_id, start_date, end_date)`

  - Invokes all lower-level forecasters and returns a unified result.

- `safe_forecast(user_id)`
  - Uses default range (e.g., next 90 days) and suppresses partial failures.

## Inputs

- `user_id`: Authenticated context
- Optional date window for projection
- Configuration flags (e.g. exclude products, override spending weights)

## Outputs

- Combined forecast document:
  ```json
  {
    "balance_projection": [ ... ],
    "category_forecast": [ ... ],
    "income_streams": [ ... ],
    "warnings": [ "Missing recurring pattern for Rent" ]
  }
  ```
````

## Internal Dependencies

- `forecast_engine`
- `forecast_balance`
- `recurring_detection`
- Logging, metrics decorators

## Known Behaviors

- Uses internal cache if inputs match previous run
- Silently degrades if forecast modules fail
- Logs warnings for user-facing debug hints

## Related Docs

- [`docs/dataflow/forecast_orchestration.md`](../../dataflow/forecast_orchestration.md)
- [`docs/frontend/pages/ForecastPage.md`](../../frontend/pages/ForecastPage.md)

```

---

Next: `forecast_stat_model.py`?
```

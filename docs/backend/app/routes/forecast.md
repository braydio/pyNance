## 📘 `forecast.py`

````markdown
# Forecast Route

## Purpose

Serves the `/api/forecast` endpoint which provides projected balances and
metadata. The route simply delegates to `ForecastOrchestrator` to assemble the
response on demand.

## Key Endpoint

- `GET /api/forecast`

## Inputs & Outputs

- **Query Params**
  - `view_type` – `'Month'` (30 days) or `'Year'` (365 days)
  - `manual_income` – optional float adjustment
  - `liability_rate` – optional float deduction

- **Output Example**

  ```json
  {
    "labels": ["May 1", "May 2", "May 3"],
    "forecast": [4200.0, 4250.0, 4300.0],
    "actuals": [4180.0, null, null],
    "metadata": {
      "account_count": 2,
      "recurring_count": 5,
      "data_age_days": 0
    }
  }
  ```

## Internal Dependencies

- `services.forecast_engine`
- `models.Transaction`
- Historical budget models and smoothing algorithms

## Known Behaviors

- Uses historical transaction patterns as basis
- Supports override parameters
- Supports merging recurring + nonrecurring projections

## Related Docs

- [`docs/forecast/FORECAST_PURPOSE.md`](../../forecast/FORECAST_PURPOSE.md)
- [`docs/dataflow/forecast_pipeline.md`](../../dataflow/forecast_pipeline.md)
````

---

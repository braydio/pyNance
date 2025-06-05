
# Forecast API Endpoint

`GET /api/forecast`

Query parameters:

- `view_type` – either `Month` (30‑day horizon) or `Year` (365‑day horizon).
- `manual_income` – optional float used as an income adjustment.
- `liability_rate` – optional float for liability deductions.
- `user_id` – provided by the frontend or session.

Response structure:

```json
{
  "labels": ["May 1", "May 2", ...],
  "forecast": [4200.0, 4250.0, ...],
  "actuals": [4200.0, null, ...],
  "metadata": {
    "account_count": 2,
    "recurring_count": 5,
    "data_age_days": 0
  }
}
```

The endpoint delegates calculation to `ForecastOrchestrator`, which compiles
recurring transactions and account history on each request.

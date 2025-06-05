
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
recurring transactions and account history on each request.  The orchestrator
uses `sql/forecast_logic.list_recurring_transactions` and
`sql/forecast_logic.get_account_history_range` to gather data before assembling
the payload.  Internal validation ensures the forecast horizon is positive, and
unit tests cover the JSON shape and edge cases.

---
Owner: Backend Team
Last Updated: 2026-02-28
Status: Active
---

# Forecast Route (`forecast.py`)

## Purpose

Provides projected balances and metadata for dashboard forecasting views by delegating computation to the forecasting services.

## Endpoints

- `GET /api/forecast` – Returns projected balances, labels, and supporting metadata for either monthly or yearly horizons.
- `POST /api/forecast/compute` – Computes a full `ForecastResult` payload with optional adjustments.

## Inputs/Outputs

- **GET /api/forecast**
  - **Inputs:** Query params `view_type` (`"Month"` or `"Year"`), optional `manual_income` (float adjustment), optional `liability_rate` (float deduction).
  - **Outputs:** JSON payload with `labels`, `forecast`, `actuals`, and `metadata` summarizing account counts, recurring items, and data age.
- **POST /api/forecast/compute**
  - **Inputs:** JSON body with:
    - `user_id` (string, required)
    - `start_date` (ISO date string, optional; defaults to today)
    - `horizon_days` (integer, optional; defaults to 30)
    - `adjustments` (list, optional; supports empty list or multiple adjustments)
  - **Outputs:** `ForecastResult` JSON containing `timeline`, `summary`, `cashflows`, `adjustments`, and `metadata`.

## Auth

- Expects an authenticated user context; relies on the standard application auth/session middleware.

## Dependencies

- `ForecastOrchestrator` and `services.forecast_engine` for projection assembly.
- Transaction history via `models.Transaction` and related budget smoothing utilities.
- `forecast.engine.compute_forecast` for stateless forecast recomputation requests.

## Behaviors/Edge Cases

- Historical transaction patterns combined with recurring and nonrecurring projections drive the response.
- Override parameters (`manual_income`, `liability_rate`) are applied to adjust the forecast.
- View selection switches horizon lengths (30 days for month, 365 days for year).
- Forecast recompute uses the most recent account snapshots and a 90-day lookback of transaction inflow/outflow aggregates.

## Sample Request/Response

```http
GET /api/forecast?view_type=Month&manual_income=200 HTTP/1.1
```

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

```http
POST /api/forecast/compute HTTP/1.1
Content-Type: application/json

{
  "user_id": "user-123",
  "start_date": "2024-01-01",
  "horizon_days": 30,
  "adjustments": [
    {
      "label": "Manual bonus",
      "amount": 250.0,
      "date": "2024-01-05",
      "adjustment_type": "manual"
    }
  ]
}
```


## Serialization notes

Latest snapshot serialization now includes explicit account investment metadata (`account_type`, `is_investment`, `investment_has_holdings`, `investment_has_transactions`) so forecast computation and downstream consumers do not need to infer investment semantics from `type` strings.

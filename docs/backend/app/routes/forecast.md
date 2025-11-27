---
Owner: Backend Team
Last Updated: 2025-11-24
Status: Active
---

# Forecast Route (`forecast.py`)

## Purpose
Provides projected balances and metadata for dashboard forecasting views by delegating computation to the forecasting services.

## Endpoints
- `GET /api/forecast` – Returns projected balances, labels, and supporting metadata for either monthly or yearly horizons.

## Inputs/Outputs
- **GET /api/forecast**
  - **Inputs:** Query params `view_type` (`"Month"` or `"Year"`), optional `manual_income` (float adjustment), optional `liability_rate` (float deduction).
  - **Outputs:** JSON payload with `labels`, `forecast`, `actuals`, and `metadata` summarizing account counts, recurring items, and data age.

## Auth
- Expects an authenticated user context; relies on the standard application auth/session middleware.

## Dependencies
- `ForecastOrchestrator` and `services.forecast_engine` for projection assembly.
- Transaction history via `models.Transaction` and related budget smoothing utilities.

## Behaviors/Edge Cases
- Historical transaction patterns combined with recurring and nonrecurring projections drive the response.
- Override parameters (`manual_income`, `liability_rate`) are applied to adjust the forecast.
- View selection switches horizon lengths (30 days for month, 365 days for year).

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

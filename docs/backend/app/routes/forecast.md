---
Owner: Backend Team
Last Updated: 2026-04-08
Status: Active
---

# Forecast Route (`forecast.py`)

## Purpose

Provides projected balances and metadata for dashboard forecasting views by delegating computation to the forecasting services.

## Endpoints

- `GET /api/forecast` – Returns projected balances, labels, and supporting metadata for either monthly or yearly horizons.
- `POST /api/forecast/compute` – Computes a full `ForecastResult` payload with optional adjustments and account include/exclude filters.

## Inputs/Outputs

- **GET /api/forecast**
  - **Inputs:** Query params `view_type` (`"Month"` or `"Year"`), optional `manual_income` (float adjustment), optional `liability_rate` (float deduction).
  - **Outputs:** JSON payload with `labels`, `forecast`, `actuals`, and `metadata` summarizing account counts, recurring items, and data age.
- **POST /api/forecast/compute**
  - **Inputs:** JSON body with:
    - `user_id` (string, required)
    - `start_date` (ISO date string, optional; defaults to today)
    - `horizon_days` (integer, optional; defaults to 30)
    - `adjustments` (list, optional; supports empty list or multiple adjustments, with optional `distribution`, `range_start`, and `range_end` for spread entries)
    - `moving_average_window` (integer, optional; 7, 30, 60, or 90; defaults to 30)
    - `normalize` (boolean, optional; normalizes historical aggregates before projection)
    - `graph_mode` (`combined`, `forecast`, or `historical`; optional chart rendering hint)
    - `included_account_ids` (list of account IDs, optional; defaults to all visible accounts)
    - `excluded_account_ids` (list of account IDs, optional; applied after includes)
  - **Outputs:** `ForecastResult` JSON containing `timeline`, `summary`, `cashflows`, `adjustments`, and `metadata`. Metadata now includes account filters (`included_account_ids`, `excluded_account_ids`), balance breakdowns (`asset_balance`, `liability_balance`, `net_balance`), aggregate contribution totals for the selected accounts, and preserved adjustment metadata such as `metadata.source_transactions` for auto-detected wage and rent entries.

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
- Auto wage detection samples up to five recent matching transactions and stores those references on each inferred adjustment under `metadata.source_transactions` so clients can render a drill-down explanation.
- Auto rent detection mirrors the wage cadence inference flow (median observed gap with bounded cadence), emits negative `auto_rent` adjustments, and publishes confidence/sampling metadata for each inferred rent row.

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

```json
{
  "user_id": "user-123",
  "start_date": "2024-01-01",
  "horizon_days": 30,
  "included_account_ids": ["acc-1", "acc-2"],
  "excluded_account_ids": ["acc-3"],
  "adjustments": []
}
```

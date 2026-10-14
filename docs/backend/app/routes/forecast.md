---
Owner: Backend Team
Last Updated: 2026-10-14
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

## V2 compute contract (`model_version: "v2"`)

`POST /api/forecast/compute` is versioned on the same URL. Omit `model_version` (or send `"v1"`) for the legacy
average-delta response, which is unchanged. Any other value except `"v2"` returns 400. V2 is implemented in
`app/services/forecast_v2_service.py` on top of `forecast/v2_core.py`, `v2_sources.py` and `v2_uncertainty.py`
(see `docs/backend/forecast/`).

### Request (V2 additions)

```json
{
  "model_version": "v2", "user_id": "alice", "start_date": "2026-11-01", "horizon_days": 90,
  "included_account_ids": ["chk"], "excluded_account_ids": [], "adjustments": [],
  "simulation": {"enabled": true, "count": 300, "seed": 12345, "cash_threshold": 500},
  "scenarios": [
    {"id": "pay-delay", "label": "Paycheck 7 days late", "changes": {"delay_income_days": 7}},
    {"id": "cut-spend", "label": "Spending down 15%", "changes": {"residual_spending_multiplier": 0.85}}
  ]
}
```

- `start_date` is the first projected day; the opening balance is the end of the previous day. It may be up to two
  years back (replay) or one year ahead. `horizon_days` 1..365 (default 30).
- `simulation`: `enabled` defaults to `false`; `count` 1..1000; integer `seed` (default 12345); `cash_threshold` >= 0.
- `scenarios`: at most 5, request-local, never stored. Allowed `changes`: `residual_spending_multiplier` (0..3),
  `income_multiplier` (0..3), `delay_income_days` (0..60) and dated `adjustments`. Unknown keys, duplicate ids and
  changes on the reserved id `baseline` return 400. Each scenario is replayed through the same ledger; probabilistic
  comparisons share the baseline's random draws, so deltas reflect the scenario rather than RNG noise.
- `adjustments` keep the V1 shape (`amount`, `date`, optional `frequency`, `distribution`, `range_start`, `range_end`).

### Response (V2)

All V1 keys (`timeline`, `summary`, `cashflows`, `adjustments`, `series`, `metadata`) are kept, with
`forecast_balance` defined as **liquid cash** (checking, savings, cash only), never net worth. Additional keys:
`model_version`, `status` (`ok` or `insufficient_data`), `liquidity` (`starting_cash`, `ending_cash`, `min_cash`,
`min_cash_date`, `first_shortfall_date`), `net_worth` (debt and investments reported separately),
`uncertainty` (`available`, risks, `sample_count`, `seed`, or `reason` when unavailable), `drivers` (scheduled events
with `origin` and `confidence_label`), `data_quality` (as-of date, history days, warnings) and `scenarios`.
Timeline rows only carry `p10`/`p50`/`p90` when a simulation produced them; there are no placeholder percentiles.

### Access and data rules

- This deployment has no session authentication on the forecast routes, so the body `user_id` is not proof of
  identity. V2 fails closed: any `included_account_ids` entry not owned by that user returns **403** (nothing is
  silently ignored) and every query is scoped by `user_id`. If real authentication is added, pass the
  authenticated id into `compute_v2_forecast` at the route.
- Data is loaded as of `start_date - 1`; later transactions and snapshots are never read. When no snapshot exists on or
  before that date: a past start returns `insufficient_data` with warnings; a present/future start falls back to the
  account's current balance and reports `anchored_to_current_balance`.
- Errors: 400 invalid input, 403 foreign accounts, 500 unexpected failure.

### Rollout and rollback

The Forecast page requests V2 by default. Roll back by building the frontend with `VITE_FORECAST_MODEL_VERSION=v1`
or by choosing "Legacy average-delta (V1)" under Advanced model controls. V1 code paths and `GET /api/forecast`
are untouched.


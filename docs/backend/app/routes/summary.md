# Summary Route

## Purpose

Provide aggregate income, expense, and net metrics for dashboard visualizations.
The route performs SQL calculations directly to avoid expensive post-processing
in the client.

## Key Endpoints

- `GET /api/summary/financial` – Return totals, trend data, and outlier
  detection for transactions over a requested date range.

## Inputs & Outputs

- Optional `start_date` and `end_date` query parameters accept `YYYY-MM-DD`
  strings; defaults cover the last 30 days.
- Responses are wrapped as `{ "status": "success", "data": { ... } }`. When no
  transactions exist the payload still returns a zeroed structure.
- Errors bubble up as `{ "status": "error", "message": str(exc) }`.

## Internal Dependencies

- SQLAlchemy models `Transaction` and `Account`
- Aggregations built with `sqlalchemy.func`, `case`, and `or_`
- `app.extensions.db.session` for query execution

## Known Behaviors

- Hidden accounts and internal transactions are excluded from calculations.
- Trend is calculated using a simple linear regression slope over net values.
- Volatility/outlier detection uses standard deviation thresholds (2σ).

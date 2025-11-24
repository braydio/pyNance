# Summary Route (`summary.py`)

## Purpose
Provide aggregate income, expense, and net metrics for dashboard visualizations through direct SQL calculations.

## Endpoints
- `GET /api/summary/financial` – Return totals, trend data, and outlier detection for transactions over a requested date range.

## Inputs/Outputs
- **GET /api/summary/financial**
  - **Inputs:** Optional `start_date` and `end_date` (`YYYY-MM-DD`) query params; defaults to last 30 days.
  - **Outputs:** `{ "status": "success", "data": { ... } }` with zeroed structures when no transactions exist; errors surface as `{ "status": "error", "message": ... }`.

## Auth
- Requires authenticated user; hidden accounts and internal transactions are excluded automatically.

## Dependencies
- SQLAlchemy models `Transaction` and `Account`.
- Aggregations built with `sqlalchemy.func`, `case`, and `or_` using `app.extensions.db.session`.

## Behaviors/Edge Cases
- Trend is calculated via linear regression over net values.
- Outlier detection uses standard deviation thresholds (2σ).

## Sample Request/Response
```http
GET /api/summary/financial?start_date=2024-04-01&end_date=2024-04-30 HTTP/1.1
```

```json
{ "status": "success", "data": { "income": 5000, "expenses": 3200, "net": 1800 } }
```

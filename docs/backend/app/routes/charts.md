## 📘 `charts.py`

```markdown
# Charts Route

## Purpose

Provides data for visualizing user financial trends over time, including category breakdowns and historical expense tracking. Routes feed frontend dashboard components.

## Key Endpoints

- `GET /charts/breakdown`: Category spending summary over a time range.
- `GET /charts/history`: Historical transaction totals (e.g., month-over-month).
- `GET /charts/balance`: Account balance time series.

## Inputs & Outputs

- **GET /charts/breakdown**

  - **Params:** `start_date`, `end_date`, `group_by` (e.g., month)
  - **Output:** `{ categories: [{ name: str, total: float }], total: float }`

- **GET /charts/history**

  - **Output:** `{ series: [{ date: str, total: float }], range: { start: str, end: str } }`

- **GET /charts/balance**
  - **Output:** `{ balances: [{ date: str, total: float }] }`

## Internal Dependencies

- `services.chart_aggregation_service`
- `models.Transaction`
- Utility functions for grouping/summing transactions

## Known Behaviors

- All endpoints support user-based scoping.
- Optimized for minimal data transfer (cached/summarized payloads).
- Handles null data gracefully.

## Related Docs

- [`docs/frontend/components/ChartPanel.md`](../../frontend/components/ChartPanel.md)
- [`docs/dataflow/chart_aggregation.md`](../../dataflow/chart_aggregation.md)
```

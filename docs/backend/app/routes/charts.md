## 📘 `charts.py`

```markdown
# Charts Route

## Purpose

Provides data for visualizing financial trends over time, including category breakdowns and historical expense tracking. Routes feed frontend dashboard components.

## Key Endpoints

- `GET /charts/category_breakdown` – Category spending summary.
- `GET /charts/daily_net` – Net income/expense per day.
- `GET /charts/cash_flow` – Aggregated income and expenses (daily or monthly).
- `GET /charts/net_assets` – Net assets, assets, and liabilities over time.
- `GET /charts/accounts-snapshot` – Current visible account balances.
- `GET|POST /charts/forecast` – Forecast vs actual balance line.

## Inputs & Outputs

- **GET /charts/category_breakdown**

  - **Params:** `start_date`, `end_date`
  - **Output:** `{ status: 'success', data: [{ category: str, amount: float, date: str }] }`

- **GET /charts/daily_net**

  - **Output:** `{ status: 'success', data: [{ date: str, net: float, income: float, expenses: float, transaction_count: int }] }`

- **GET /charts/cash_flow**

  - **Params:** `granularity` (`daily` or `monthly`), optional `start_date`, `end_date`
  - **Output:** `{ status: 'success', data: [{ date: str, income: float, expenses: float }], metadata: { total_income: float, total_expenses: float, total_transactions: int } }`

- **GET /charts/net_assets**

  - **Output:** `{ status: 'success', data: [{ date: str, net_assets: float, assets: float, liabilities: float }] }`

- **GET /charts/accounts-snapshot**

  - **Output:** `[ { account_id: str, name: str, institution_name: str, balance: float, type: str, subtype: str } ]`

- **GET|POST /charts/forecast**

  - **Params:** `view_type` (`Month` or `Year`), optional `manual_income`, `liability_rate`
  - **Output:** `{ labels: [str], forecast: [float], actuals: [float], metadata: { ... } }`

## Internal Dependencies

- `services.chart_aggregation_service`
- `models.Transaction`
- Utility functions for grouping/summing transactions

## Known Behaviors

- Optimized for minimal data transfer (cached/summarized payloads).
- Handles null data gracefully.

## Related Docs

- [`docs/frontend/components/ChartPanel.md`](../../frontend/components/ChartPanel.md)
- [`docs/dataflow/chart_aggregation.md`](../../dataflow/chart_aggregation.md)
```

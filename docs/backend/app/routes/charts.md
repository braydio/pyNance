---
Owner: Backend Team
Last Updated: 2026-07-16
Status: Active
---

# Charts Route (`charts.py`)

## Purpose

Provide chart-ready financial summaries for dashboard components, covering category breakdowns, net cash movement, and forecast overlays.

## Endpoints

- `GET /charts/category_breakdown` – Category spending summary.
- `GET /charts/category_breakdown_tree` – Hierarchical expense totals used by the dashboard category chart.
- `GET /charts/category_transactions` – Unpaginated expense transactions represented by selected category bars.
- `GET /charts/merchant_breakdown` – Expense totals grouped by merchant.
- `GET /charts/merchant_transactions` – Unpaginated expense transactions represented by a merchant bar.
- `GET /charts/tag_metrics` – Tag totals and counts summary.
- `GET /charts/daily_net` – Net income/expense per day.
- `GET /charts/cash_flow` – Aggregated income and expenses by day or month.
- `GET /charts/net_assets` – Net assets, assets, and liabilities over time.
- `GET /charts/accounts-snapshot` – Current visible account balances.
- `GET /charts/forecast` – Forecast vs. actual balance timeseries.

## Inputs/Outputs

- **GET /charts/category_breakdown**
  - **Inputs:** `start_date`, `end_date` query params.
  - **Outputs:** `{ "status": "success", "data": [{ "category": str, "amount": float, "date": str }] }`.
- **GET /charts/category_breakdown_tree**
  - **Inputs:** Optional `start_date`, `end_date`, and `top_n` query params.
  - **Outputs:** Hierarchical parent/detail category totals with the category IDs represented by each bar.
- **GET /charts/category_transactions**
  - **Inputs:** Required comma-delimited `category_ids`; optional `start_date` and `end_date`.
  - **Outputs:** All visible, non-internal expense transactions matching those category IDs and the inclusive date range.
- **GET /charts/merchant_breakdown**
  - **Inputs:** Optional `start_date`, `end_date`, and `top_n` query params.
  - **Outputs:** Merchant expense totals for visible, non-internal transactions in the inclusive date range.
- **GET /charts/merchant_transactions**
  - **Inputs:** Required `merchant`; optional `start_date` and `end_date`.
  - **Outputs:** All visible, non-internal expense transactions represented by that merchant bar.
- **GET /charts/tag_metrics**
  - **Inputs:** `start_date`, `end_date` query params.
  - **Outputs:** `{ "status": "success", "data": [{ "tag": str, "total": float, "count": int }] }`.
- **GET /charts/daily_net**
  - **Inputs:** Optional date filters depending on client.
  - **Outputs:** `{ "status": "success", "data": [{ "date": str, "net": float, "income": float, "expenses": float, "transaction_count": int }] }`.
- **GET /charts/cash_flow**
  - **Inputs:** `granularity` (`daily` or `monthly`), optional `start_date`, `end_date`.
  - **Outputs:** `{ "status": "success", "data": [{ "date": str, "income": float, "expenses": float }], "metadata": { "total_income": float, "total_expenses": float, "total_transactions": int } }`.
- **GET /charts/net_assets**
  - **Outputs:** `{ "status": "success", "data": [{ "date": str, "net_assets": float, "assets": float, "liabilities": float }] }`.
- **GET /charts/accounts-snapshot**
  - **Outputs:** `[ { "account_id": str, "name": str, "institution_name": str, "balance": float, "type": str, "subtype": str } ]`.
- **GET /charts/forecast**
  - **Inputs:** `view_type` (`Month` or `Year`), optional `manual_income`, optional `liability_rate`.
  - **Outputs:** `{ "labels": [str], "forecast": [float], "actuals": [float], "metadata": { ... } }`.

## Auth

- Uses the standard authenticated user context to scope transactions and balances.

## Dependencies

- `services.chart_aggregation_service` for summarization.
- `models.Transaction` for raw transaction data.
- Helper utilities for grouping and summing cash flow.

## Behaviors/Edge Cases

- Responses are optimized for minimal payload size and tolerate empty result sets.
- Daily, category, and merchant chart ranges use inclusive calendar dates. Their drill-down data excludes hidden
  accounts and internal transfers; category and merchant drill-downs include only expenses that contribute to the
  selected bar.
- Forecast endpoint mirrors the `/api/forecast` logic for overlayed views.

## Sample Request/Response

```http
GET /charts/cash_flow?granularity=daily&start_date=2024-04-01&end_date=2024-04-07 HTTP/1.1
```

```json
{
  "status": "success",
  "data": [
    { "date": "2024-04-01", "income": 250.0, "expenses": 180.0 },
    { "date": "2024-04-02", "income": 0.0, "expenses": 90.0 }
  ],
  "metadata": {
    "total_income": 250.0,
    "total_expenses": 270.0,
    "total_transactions": 6
  }
}
```

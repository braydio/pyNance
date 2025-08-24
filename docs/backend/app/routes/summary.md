## 📘 `summary.py`

````markdown
# Summary Route

## Purpose

Aggregates income and expense transactions over a date range and derives higher level metrics for dashboard display.

## Key Endpoints

- `GET /summary/financial` – totals and statistical metrics for the requested date window.

## Inputs & Outputs

- **GET /summary/financial**
  - **Params:** optional `start_date`, `end_date` (YYYY-MM-DD)
  - **Output:**
    ```json
    {
      "status": "success",
      "data": {
        "totalIncome": 123.45,
        "totalExpenses": -67.89,
        "totalNet": 55.56,
        "highestIncomeDay": { "date": "2024-01-03", "amount": 300.0 },
        "highestExpenseDay": { "date": "2024-01-02", "amount": -200.0 },
        "trend": 10.5,
        "volatility": 50.0,
        "outliers": ["2024-01-02"]
      }
    }
    ```

## Internal Dependencies

- `models.Transaction`
- `utils.finance_utils.display_transaction_amount`
- SQLAlchemy via `extensions.db`

## Known Behaviors

- Ignores internal transfers.
- Defaults to the previous 30 days when no range is supplied.
- Outliers flagged when net values deviate by more than two standard deviations.

## Related Docs

- [`docs/frontend/FINANCIAL_SUMMARY.md`](../../frontend/FINANCIAL_SUMMARY.md)
````

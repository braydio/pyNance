## 📘 `forecast.py`

````markdown
# Forecast Route

## Purpose

Handles generation and delivery of forward-looking financial forecasts. This includes monthly budget projections, predicted spending trends, and income estimation.

## Key Endpoints

- `GET /forecast/summary`: Retrieve a forecasted overview of upcoming finances.
- `GET /forecast/by-category`: Detailed forecast per spending category.
- `POST /forecast/custom`: Accepts user input to customize forecasting models.

## Inputs & Outputs

- **GET /forecast/summary**

  - **Params:** `month`, `account_ids[]` (optional filters)
  - **Output:**
    ```json
    {
      "total_income": 3500,
      "total_expense": 2850,
      "net": 650,
      "projected_savings": 500
    }
    ```

- **GET /forecast/by-category**

  - **Output:**
    ```json
    [
      { "category": "Groceries", "expected": 420 },
      { "category": "Utilities", "expected": 150 }
    ]
    ```

- **POST /forecast/custom**
  - **Input:** `{ inputs: { income: number, goals: {...} } }`
  - **Output:** Tailored forecast object

## Internal Dependencies

- `services.forecast_engine`
- `models.Transaction`
- Historical budget models and smoothing algorithms

## Known Behaviors

- Uses historical transaction patterns as basis
- Allows override via user-specific parameters
- Supports merging recurring + nonrecurring projections

## Related Docs

- [`docs/forecast/FORECAST_PURPOSE.md`](../../forecast/FORECAST_PURPOSE.md)
- [`docs/dataflow/forecast_pipeline.md`](../../dataflow/forecast_pipeline.md)
````

---

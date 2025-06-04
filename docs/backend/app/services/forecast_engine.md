## 📘 `forecast_engine.py`

````markdown
# Forecast Engine Service

## Purpose

The central computation engine responsible for producing transaction-level financial forecasts based on user trends, behavior modeling, and detected patterns. Integrates balance, income, and spending projections.

## Key Responsibilities

- Load and preprocess historical transaction data
- Estimate category-level future spending
- Forecast recurring income and expense flows
- Aggregate forecasts into structured models

## Primary Functions

- `run_forecast(user_id, range_start, range_end)`

  - Returns: Full structured forecast object (balance, income, expenses)

- `analyze_spending_patterns(transactions)`

  - Clusters transactions to extract predictable patterns

- `predict_category_expense(category, month)`
  - Outputs a single number prediction per category for the future month

## Inputs

- Normalized user transaction data
- Recurring transaction profiles (linked via user_id)
- User preferences (if any customization enabled)

## Outputs

- Forecast object including:
  ```json
  {
    "income": 4300,
    "expenses": 2780,
    "projected_balance": 520,
    "by_category": [
      { "category": "Rent", "expected": 1200 },
      { "category": "Groceries", "expected": 400 }
    ]
  }
  ```
````

## Internal Dependencies

- `forecast_stat_model`, `forecast_balance`, `recurring_detection`
- `models.Transaction`, `models.Forecast`
- Math/stat libs (e.g., numpy, sklearn, statsmodels)

## Known Behaviors

- Can be batched for background processing
- Allows weight overrides per category
- Result structure reused by frontend and export tools

## Related Docs

- [`docs/dataflow/forecast_pipeline.md`](../../dataflow/forecast_pipeline.md)
- [`docs/frontend/components/ForecastSummary.md`](../../frontend/components/ForecastSummary.md)

```

---

Next: `forecast_orchestrator.py`?
```

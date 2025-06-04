# backend/app/services Documentation

---

## 📘 `forecast_stat_model.py`

```markdown
# Forecast Statistical Model Service

## Purpose

Provides statistical and machine-learning-backed models for forecasting user financial behavior. Acts as a support module for the `forecast_engine` and related components, delivering numeric predictions per category and trendline.

## Key Responsibilities

- Model future spending patterns using regressions or time series
- Fit statistical models per category (linear, exponential smoothing, etc.)
- Provide adjustable confidence windows

## Primary Functions

- `predict_category_trend(transactions, category, range)`

  - Returns forecasted value for next period with optional confidence interval

- `fit_model(transactions, model_type="linear")`

  - Produces a trend model over time

- `explain_forecast(category)`
  - Outputs reasons behind predictions for interpretability

## Inputs

- Historical transactions segmented by category and date
- Optional feature flags (seasonality, weight boosting)

## Outputs

- Single-value or array predictions
- Confidence bands and diagnostic messages
- Model parameters (weights, residuals)

## Internal Dependencies

- `pandas`, `numpy`, `sklearn`, `statsmodels`
- Transaction aggregators

## Known Behaviors

- Automatically switches models if performance drops
- Supports visualization overlays (e.g., dotted projections)
- Refit triggered monthly or manually via admin tools

## Related Docs

- [`docs/dataflow/statistical_forecasting.md`](../../dataflow/statistical_forecasting.md)
- [`docs/models/ForecastModel.md`](../../models/ForecastModel.md)
```

---

Next: `recurring_bridge.py`?

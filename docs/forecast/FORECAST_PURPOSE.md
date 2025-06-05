# Forecasting Module Overview

**Directory:** `backend/app/services/`
**Modules:**

- `forecast_engine.py`
- `forecast_stat_model.py`
- `forecast_orchestrator.py`

---

## Purpose

The forecasting module in `pyNance` is responsible for projecting a user's financial trajectory. This includes:

- Predicting **recurring financial transactions** (e.g. rent, subscriptions, paychecks)
- Simulating **future account balances** based on these projections
- Optionally applying **statistical time-series models** (like ARIMA) for alternative or hybrid forecasts

---

## Components

### 1. `forecast_engine.py`

Implements the **rule-based forecast engine**:

- Uses `RecurringTransaction` entries from the database
- Projects each transaction forward according to its frequency and next due date
- Aggregates forecasted transactions to simulate **daily net balances**
- Depends on the latest actual balances from `AccountHistory`

```python
forecast_engine = ForecastEngine(db)
forecast_engine.forecast_balances(horizon_days=60)
```

### 2. `forecast_stat_model.py`

Implements a **statistical forecast engine**:

- Based on ARIMA (AutoRegressive Integrated Moving Average)
- Operates on a `pandas.Series` time series (typically balances or totals)
- Can forecast future values and evaluate its prediction accuracy using MSE

```python
stat_engine = ForecastEngine(order=(2,1,2))
stat_engine.fit(balance_series)
stat_engine.forecast(steps=30)
```

### 3. `forecast_orchestrator.py`

A **controller class** that unifies both engines:

- Delegates to rule-based or stat-based forecasts depending on method
- Abstracts method switching for API or interface calls

```python
orchestrator = ForecastOrchestrator(db)
orchestrator.forecast(method='rule', days=60)
orchestrator.forecast(method='stat', days=30, stat_input=balance_series)
```

---

## Design Rationale

This hybrid architecture was chosen to:

- Leverage **explicit, known recurring logic** (e.g. payroll, bills)
- Allow **advanced analytics or overlays** via ARIMA or ML
- Ensure modularity and future flexibility

The rule-based method is personalized and interpretable.
The stat-model method is predictive and empirical.

This dual capability enables:

- Exploratory modeling
- Fallback logic if recurring transaction data is sparse
- Ensemble techniques in the future

---

## Scope

This module currently covers:

- Forecasting **recurring transaction schedules**
- Forecasting **projected balances per account**
- Statistical ARIMA-based forecasts of numeric series (optional)

It does **not yet cover**:

- One-off or seasonal transaction predictions
- Variable income prediction or inflation modeling
- Interactive UI hooks or feedback loops (TBD)

---

## Next Steps

1. **Refine API endpoint** – `/api/forecast` now uses `ForecastOrchestrator`; continue improving validation and metadata.
2. **Wire frontend** to visualize net forecast trajectory
3. **Integrate actual vs. projected comparison** using historical backtests
4. Build `recurring_detection.py` to dynamically populate recurring records
5. Extend orchestration to support **ensemble** or hybrid forecasts

---

## Authors

This forecasting subsystem was collaboratively designed based on a combination of:

- Domain-specific heuristics (for recurring cash flow)
- Financial modeling practices
- Time-series forecasting conventions (ARIMA)

---

For updates, see:

- `forecast_refactor_log.md`
- `pyNance_tasklog.json`

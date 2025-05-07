---

# 📘 pyNance Backend Forecast Integration Guide

## Index

1. **📚 Existing Route Overview**
2. **🧠 Data Model Analysis (models.py)**
3. **⚙️ Recommendation: Forecast Integration Strategy**
4. **🧩 Proposed API Design**
5. **⚠️ Potential Issues & Considerations**
6. **🛠 Next Steps**

---

## 1. 📚 Existing Route Overview

### Route Files:

- **`accounts.py`**: Core account CRUD, upserts, linking to users/items.
- **`transactions.py`**: All Plaid & Teller transactions sync and queries.
- **`recurring.py`**: Existing logic for storing recurring predictions.
- **`charts.py`**: High-level reporting endpoints; could house forecast aggregations.
- **`manual_io.py`**: Dev + test endpoints for data ingestion.

### Candidate Endpoints:

- **GET `/api/recurring`**: Returns user recurring transactions. ✅ Candidate input to forecast engine.
- **GET `/api/transactions/history`**: Already fetching account balances. ✅ Actuals source.
- **GET `/api/charts/networth`**: Runs aggregation. 🧠 Possibly extended with forecasts.

---

## 2. 🧠 Data Model Analysis (`models.py`)

### Key Tables:

- **`accounts`** → Core metadata & balance field.
- **`account_history`** → Date-wise balance snapshots (used for “actuals” in forecast).
- **`recurring_transactions`** → User input / inferred patterns (used for “forecast line”).
- **`transactions`** → Ground-truth historical transactions.

### Missing?

- No dedicated **forecast results table**, but...

  - Forecasts can be **calculated on-the-fly** or
  - **Cached per viewType** and date range if needed later.

---

## 3. ⚙️ Recommendation: Forecast Integration Strategy

### ✅ Use live data:

- Real forecasts are best generated _live_ from:

  - `recurring_transactions`
  - `account_history`
  - optional manual income/liability modifiers

### ❌ Don’t create `forecast_results` table yet

- Start lightweight.
- Forecasts are _ephemeral_, view-dependent, and parameter-sensitive.

---

## 4. 🧩 Proposed API Design

### Forecast Calculation Route (NEW):

```
GET /api/forecast/summary
Params:
  - user_id (implicit from session or param)
  - viewType (Month|Year)
  - manualIncome
  - liabilityRate
```

### Returns:

```json
{
  "labels": ["May 1", "May 2", ..., "May 31"],
  "forecast": [4200, 4280, ...],
  "actuals": [4200, 4190, ...],
  "metadata": {
    "account_count": 3,
    "total_income_sources": 2,
    "discrepancy": 128.75
  }
}
```

---

## 5. ⚠️ Potential Issues & Considerations

- 🧪 **Data freshness**: Ensure balances are up to date (`account_history`).
- 🔁 **Recurring noise**: User-edited vs. auto-detected should be tagged.
- 🔐 **Auth**: Forecast route must be protected (tie to session/user_id).
- 📆 **Calendar alignment**: Use `date-fns` or `pendulum` to align labels properly backend-side if needed.

---

## 6. 🛠 Next Steps

### Backend:

- [ ] Scaffold `/api/forecast/summary` route in `charts.py`
- [ ] Query:

  - User’s recurring txs
  - User’s account history

- [ ] Use the logic in `useForecastEngine.ts` (adapted) in Python
- [ ] Return the labeled forecast vs. actual line

### Frontend:

- [x] Mock integration with engine
- [ ] Wire Axios to new route for live data
- [ ] Swap mock engine with API call

---

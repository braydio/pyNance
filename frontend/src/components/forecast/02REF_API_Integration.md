# 📡 Forecast Engine Module 2: Backend API & Integration

This module defines the **forecast engine API design**, backend routing strategy, and key integration considerations for live forecast generation in `pyNance`.

---

## 🧭 Forecast API Strategy

### ✅ Preferred Method: **Live Calculation (No Persistent Table)**

- Pulls fresh data on every request.
- Uses:
  - `recurring_transactions`
  - `account_history`
  - optional: `transactions` (for fallback actuals)

- Manual inputs like `manualIncome`, `liabilityRate` sent as adjustments to the compute payload

### ❌ Optional Later: `forecast_snapshots` Table (for caching)

- Useful if dashboard becomes slow
- Stores view-specific cached responses

---

## 📑 Proposed Route Design

### `GET /api/forecast`

| Param            | Type   | Description                 |
| ---------------- | ------ | --------------------------- |
| `user_id`        | string | Implicit from session/auth  |
| `view_type`      | string | `'Month'` or `'Year'`       |
| `manual_income`  | float  | Optional income override    |
| `liability_rate` | float  | Optional liability modifier |

#### Response:

```json
{
  "labels": ["May 1", "May 2", "May 3", ...],
  "forecast": [4200.0, 4320.0, 4350.0, ...],
  "actuals": [4200.0, 4280.0, null, ...],
  "metadata": {
    "account_count": 3,
    "recurring_count": 5,
    "data_age_days": 0
  }
}
```

### `POST /api/forecast/compute`

| Field          | Type   | Description                             |
| -------------- | ------ | --------------------------------------- |
| `user_id`      | string | Required user identifier                |
| `start_date`   | string | Optional ISO start date                 |
| `horizon_days` | number | Optional horizon length in days         |
| `adjustments`  | array  | Manual/recurring adjustments (optional) |

#### Example payload:

```json
{
  "user_id": "user-123",
  "start_date": "2024-01-01",
  "horizon_days": 30,
  "adjustments": [
    {
      "label": "Manual income",
      "amount": 200,
      "date": "2024-01-01",
      "frequency": "daily",
      "adjustment_type": "manual"
    }
  ]
}
```

#### Forecast aspect series

`POST /api/forecast/compute` also returns a top-level `series` object keyed by stable aspect names.
Each entry includes an `id`, `label`, and ordered daily `points`. The frontend now reads these
series directly for:

- `realized_income`
- `manual_adjustments`
- `spending`
- `debt_totals`

This keeps `timeline`, `cashflows`, and `summary` available for backwards compatibility while
removing the need to infer chart datasets from flat cashflow rows.

---

## ⚙️ Backend Flow

1. 🔐 **Authenticate User**
   - Derive `user_id` via token/session

2. 📥 **Pull Inputs**
   - From DB:
     - `recurring_transactions`
     - `account_history`
     - `transactions` (optional)

   - From frontend:
     - `manualIncome`, `liabilityRate`

3. 🧠 **Generate Forecast Line**
   - Recurrence-based projection per date

4. 🧮 **Generate Actuals Line**
   - Prefer `account_history`
   - Fallback to `sum(transactions by date)`

5. 🚀 **Return Aligned Arrays**
   - Includes metadata for diagnostics/debug

---

## 🛑 Considerations

- ⏱️ Performance: optimize queries for range filtering
- 🔐 Security: route should be protected by auth middleware
- 🧪 Testing: seed database with recurring + history records
- 📅 Date Handling: use `pendulum` or `dateutil` for consistency

---

## 🛠️ Next Steps (Module 2)

- [ ] Implement `/api/forecast` route in `charts.py`
- [ ] Reuse logic from `useForecastEngine.ts` (ported to Python)
- [ ] Add unit test coverage for forecast accuracy
- [ ] Document endpoint in API spec / Swagger

---

_This is Module 2 of 2. Combined with Module 1, this forms a full-stack specification for forecast rendering._

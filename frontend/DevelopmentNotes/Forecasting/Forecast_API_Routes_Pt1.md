## Forecast Engine Routing to Backend API

# 📘 Forecast Engine Integration Design (Backend)

## 📑 Index

- [1. Routing Overview](#1-routing-overview)
- [2. Relevant Database Models](#2-relevant-database-models)
- [3. Forecast Engine Design Options](#3-forecast-engine-design-options)
- [4. Recommended Strategy](#4-recommended-strategy)
- [5. Proposed API Route](#5-proposed-api-route)
- [6. Backend Processing Flow](#6-backend-processing-flow)
- [7. Summary & Next Steps](#7-summary--next-steps)

---

## 1. Routing Overview

**Key Existing Routes:**

| Route                      | Description                                               |
| -------------------------- | --------------------------------------------------------- |
| `/accounts/`               | Account balance and metadata                              |
| `/plaid_accounts/`         | Link/auth token management                                |
| `/transactions/`           | Real transaction history                                  |
| `/recurring_transactions/` | Manually or automatically defined repeat financial events |
| `/account_history/`        | Balance per account per date                              |

---

## 2. Relevant Database Models

### 🗃️ Key Tables Used for Forecast Logic:

- **`recurring_transactions`**: defines predictable financial flows (rent, salary, etc.)
- **`account_history`**: actual balances used for “realized” or actuals line
- **`transactions`**: source of actual money movements
- **`accounts`**: active balances and metadata
- **`plaid_items`**: auth context, maps user to provider tokens

---

## 3. Forecast Engine Design Options

### 📌 Option 1: Create a new `forecast_snapshots` table

```sql
CREATE TABLE forecast_snapshots (
  id INTEGER PRIMARY KEY,
  user_id VARCHAR(64),
  view_type VARCHAR(16), -- 'Month' or 'Year'
  label VARCHAR(128),
  date DATE,
  forecast_amount FLOAT,
  actual_amount FLOAT,
  created_at DATETIME
);
```

**Pros:**

- Enables caching and historical tracking
- Quick access for heavy dashboard rendering

**Cons:**

- Risk of stale data if not refreshed regularly
- Needs extra cleanup logic

---

### 📌 Option 2: Compute forecast live

- Pull real-time from:

  - `recurring_transactions`
  - `account_history`
  - (Optionally) `transactions`

**Pros:**

- Always reflects latest data
- No overhead for storage or expiration

**Cons:**

- Slightly slower performance on large datasets
- Must tune query performance

---

## 4. Recommended Strategy

**✔️ Start with Option 2 (Live Calculation)**

Use composable-style logic in the backend with:

- `recurring_transactions` to calculate expected values
- `account_history` as the baseline for actuals
- `manual_income` and `liability_rate` passed from frontend

Only add snapshot caching (`forecast_snapshots`) if performance demands it later.

---

## 5. Proposed API Route

### `GET /api/forecast`

| Parameter        | Type   | Description              |
| ---------------- | ------ | ------------------------ |
| `user_id`        | string | Currently logged-in user |
| `view_type`      | string | `'Month'` or `'Year'`    |
| `manual_income`  | float  | Optional override        |
| `liability_rate` | float  | Optional override        |

#### Response:

```json
{
  "labels": ["May 1", "May 2", "May 3", "..."],
  "forecast": [4200.0, 4320.0, 4350.0, "..."],
  "actuals": [4200.0, 4280.0, null, "..."]
}
```

---

## 6. Backend Processing Flow

1. 🔐 Verify user’s identity via `user_id`
2. 📥 Fetch all related:

   - `recurring_transactions`
   - `account_history`

3. 🧠 Apply forecast logic

   - Match to current view (`Month`/`Year`)
   - Generate `labels`
   - Create `forecastLine[]`
   - Pull or estimate `actualLine[]`

4. 🚀 Return JSON for frontend rendering

---

## 7. Summary & Next Steps

### ✅ What’s Ready

- Data models align well with forecast engine structure
- Forecast engine composable can be ported to Flask

### 🔧 Action Plan

- [ ] Build `GET /api/forecast`
- [ ] Reuse `useForecastEngine.ts` logic in Python
- [ ] Integrate frontend chart to hit this endpoint

---

Would you like me to now scaffold the `GET /api/forecast` backend route using this design?

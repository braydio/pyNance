# 󰔟 Forecast Engine: Goal-Based Implementation Plan

A step-by-step guide to implementing a forecast engine using the `pyNance` repo, from concept to production deployment.

---

## 󰲢 Goal 1: Ingest & Structure Data

### 󰄬 Objective:

Build a robust data ingestion pipeline for transactions and balances.

### 󰐥 Steps:

- [ ] Set up Plaid/Teller API integration.
- [ ] Fetch and normalize transaction data.
- [ ] Store transactions in `transactions` table.
- [ ] Fetch and store account balance snapshots in `account_history`.
- [ ] Define SQLAlchemy models in `models.py`.
- [ ] Schedule daily sync via backend cron or task runner.

---

## 󰲢 Goal 2: Detect Recurring Patterns

### 󰄬 Objective:

Identify repeating charges/income for forecast generation.

### 󰐥 Steps:

- [ ] Create `findRecurring()` utility in `utils/`.
- [ ] Group by `description` and interval similarity.
- [ ] Output pattern structure:

  ```ts
  {
    label, amount, frequency, start_date
  }
  ```

- [ ] Store and manage recurring rules.
- [ ] Write unit tests for recurrence logic.

---

## 󰲢 Goal 3: Generate Forecast Data

### 󰄬 Objective:

Produce future forecast line using recurrence + manual inputs.

### 󰐥 Steps:

- [ ] Create forecast generator service in `services/`.
- [ ] Combine recurring rules and user-defined inputs.
- [ ] Generate daily forecasted balances.
- [ ] Store forecast cache per user/account.
- [ ] Add fallback logic for no recurring data.

---

## 󰲢 Goal 4: Derive Actuals

### 󰄬 Objective:

Generate historical actuals using transaction flow or balance snapshots.

### 󰐥 Steps:

- [ ] Aggregate `account_history` by date for balances.
- [ ] Fallback: sum `transactions` per day.
- [ ] If both available: align and log differences.
- [ ] Prepare actuals series for chart rendering.

---

## 󰲢 Goal 5: Create Backend API

### 󰄬 Objective:

Expose data for frontend via REST API.

### 󰐥 Steps:

- [ ] Add endpoints in `routes/forecast.py`:

  - `GET /forecast`
  - `GET /actuals`
  - `GET /transactions`

- [ ] Return structured JSON for each line.
- [ ] Handle loading state and error fallback.
- [ ] Write tests for endpoints.

---

## 󰲢 Goal 6: Render Forecast in Frontend

### 󰄬 Objective:

Visualize actual and forecast data interactively.

### 󰐥 Steps:

- [ ] Build `ForecastChart.vue` using Chart.js/D3.
- [ ] Plot forecast vs actual with date-bound cutoff.
- [ ] Add monthly/yearly toggle.
- [ ] Embed in `Dashboard.vue`.
- [ ] Fetch data via Vuex store from backend.

---

## 󰲢 Goal 7: Deploy & Monitor

### 󰄬 Objective:

Ship and maintain the feature in production.

### 󰐥 Steps:

- [ ] Test complete flow using mock/test data.
- [ ] Integrate with production Plaid/Teller credentials.
- [ ] Deploy backend and frontend changes.
- [ ] Monitor logs, set up alerting on sync failures.
- [ ] Schedule periodic review of forecast accuracy.

---

## 󰄳 Success Criteria

- Transactions & balances ingested daily.
- Recurring entries identified with >90% accuracy.
- Forecast and actuals chart loads for all users.
- Backend responds within 200ms per endpoint.
- Forecast accuracy within ±5% tolerance monthly.

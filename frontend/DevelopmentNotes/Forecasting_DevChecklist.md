# 󰔟 Forecast Engine: Goal-Based Implementation Plan

A step-by-step guide to implementing a forecast engine using the `pyNance` repo, from concept to production deployment.

- Detailed notes in frontned/DevelopmentNotes/Forecast/

---

## 󰲢 Goal 1: Ingest & Structure Data

### 󰄬 Objective

Build a robust data ingestion pipeline for transactions and balances.

### 󰐥 Steps

- [x] Set up Plaid/Teller API integration.
- [x] Fetch and normalize transaction data.
- [x] Store transactions in `transactions` table.
- [ ] Fetch and store account balance snapshots in `account_history`.
- [x] Define SQLAlchemy models in `models.py`.
- [ ] Schedule daily sync via backend cron or task runner.

---

## 󰲢 Goal 2: Build and Validate Frontend Visuals

### 󰄬 Objective

Render forecast and actuals UI with mock data matching the final backend format.

### 󰐥 Steps

- [ ] Build `ForecastChart.vue` using Chart.js/D3.
- [ ] Plot forecast vs actual with mock data.
- [ ] Add monthly/yearly toggle.
- [ ] Embed chart in `Dashboard.vue`.
- [ ] Validate frontend rendering logic for key calculations (totals, rates, deltas).

---

## 󰲢 Goal 3: Implement Forecast Calculation Logic

### 󰄬 Objective

Build all frontend-facing logic for forecast generation, manual adjustments, and rate modeling.

### 󰐥 Steps

- [ ] Create forecast calculator service in `services/`.
- [ ] Add time period logic and interest rate handling.
- [ ] Support manual event/adjustment inputs.
- [ ] Generate daily forecasted balances from base logic.
- [ ] Prepare forecast data shape for chart compatibility.

---

## 󰲢 Goal 4: Derive Actuals in Pipeline

### 󰄬 Objective

Perform actual calculations automatically during the sync pipeline, not just at API call time.

### 󰐥 Steps

- [ ] Aggregate `account_history` by date for balances.
- [ ] Fallback: sum `transactions` per day.
- [ ] If both available: align and log differences.
- [ ] Store `actuals` as part of forecast cache or sync metadata.

---

## 󰲢 Goal 5: Detect Recurring Patterns

### 󰄬 Objective

Identify repeating charges/income for use in forecasting.

### 󰐥 Steps

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

## 󰲢 Goal 6: Create Backend API

### 󰄬 Objective

Expose forecast and actuals data for frontend via REST API.

### 󰐥 Steps

- [ ] Add endpoints in `routes/forecast.py`:

  - `GET /forecast`
  - `GET /actuals`
  - `GET /transactions`

- [ ] Return structured JSON for each line.
- [ ] Handle loading state and error fallback.
- [ ] Write tests for endpoints.

---

## 󰲢 Goal 7: Deploy & Monitor

### 󰄬 Objective

Ship and maintain the feature in production.

### 󰐥 Steps

- [ ] Test complete flow using mock/test data.
- [x] Integrate with production Plaid/Teller credentials.
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

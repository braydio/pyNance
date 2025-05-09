dev_notes = f"""

# 🛠️ Forecasting Development Notes – pyNance

_Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_

---

## 📑 Index

1. [Overview](#overview)
2. [Checklist](#checklist)
3. [Forecast API Endpoints](#forecast-api-endpoints)
4. [Engine Architecture](#engine-architecture)
5. [Database Tables](#database-tables)
6. [Pending Enhancements](#pending-enhancements)
7. [Testing & Dev](#testing--dev)

---

## 📘 Overview

The forecasting module provides a dynamic view of projected vs. realized financial activity, using real user data from accounts, recurring transactions, and historical balances. The engine works across two views (Month & Year) and supports manual inputs for forecast overrides.

---

## ✅ Checklist

- [x] Initial forecast route `/api/forecast/summary`
- [x] Forecast composable `useForecastEngine.ts`
- [x] Vue chart component displaying forecast vs. actuals
- [x] Toggle for Month/Year views
- [x] Integration with recurring transactions
- [x] Integration with account history
- [x] Manual income override
- [x] Liability rate override
- [x] Styling consistent with Dashboard.vue
- [x] ForecastLayout and chart logic working with mock data
- [x] Route: `/api/forecast/calculate` scaffolded
- [x] ForecastPage.vue mock test harness
- [ ] Live engine integration
- [ ] Backfill forecast route logic with real transactions
- [ ] Add investment performance scaffolding
- [ ] Advanced discrepancy analysis
- [ ] Edge case validation & error boundaries

---

## 📡 Forecast API Endpoints

### `/api/forecast/summary` (GET)

- Query Params:

  - `user_id`
  - `viewType` = 'Month' | 'Year'
  - `manualIncome` (optional)
  - `liabilityRate` (optional)

- Returns:
  - Labels
  - Forecast values
  - Actuals values
  - Metadata (account count, income sources, discrepancy)

---

### `/api/forecast/calculate` (POST)

- Body:

  - `user_id`
  - `viewType`
  - `manualIncome`
  - `liabilityRate`

- Returns same as summary but can include experimentations or advanced config.

---

## ⚙️ Engine Architecture

- **Input Data Sources**:

  - `accounts`, `account_history`, `recurring_transactions`, `transactions`

- **Engine Composable**:
  - `useForecastEngine` (Vue composable)
  - Accepts mock/real recurringTxs, account history, manual overrides
  - Generates `forecastLine`, `actualLine`, `labels`

---

## 🧱 Database Tables

Relevant models:

- `accounts`
- `account_history`
- `recurring_transactions`
- `transactions`
- (eventual: `investments`)

---

## 🚀 Pending Enhancements

- Integrate actual `/transactions` table into engine
- Create helper to flatten recurring logic into daily/monthly aggregates
- Real investment performance factors
- Cacheable precomputed forecasts (maybe stored in new `forecast_snapshots` table)
- CLI dev utility to simulate forecasts
- Full forecast adjustments log per-user

---

## 🧪 Testing & Dev

- ForecastMockPage.vue provides visual harness
- ForecastLayout.vue is main consumer
- Real-time switch between mock and live data
- Forecast composable accepts both `ref` and direct data

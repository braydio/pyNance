# 🛠️ Forecast Engine Module 3: Development & Enhancement Tracker

_Last synced: 2025-05-09_

This module centralizes **forecasting development progress**, dev-mode utilities, endpoint scaffolds, and future enhancements for the `pyNance` forecast system.

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

The forecasting module projects future account balances and overlays them against real transaction history. It supports manual override inputs and view-based toggling (Month/Year) and integrates tightly with backend and Vue-based frontend systems.

---

## ✅ Checklist

- [x] `/api/forecast/summary` endpoint (GET)
- [x] `useForecastEngine.ts` composable
- [x] Forecast vs. Actual chart component
- [x] Month/Year toggle logic
- [x] Integration with `recurring_transactions`
- [x] Integration with `account_history`
- [x] Manual income override handling
- [x] Liability rate override handling
- [x] Layout + styling integration with `Dashboard.vue`
- [x] Mock engine hooked to `ForecastPage.vue`
- [x] `/api/forecast/calculate` (POST) scaffolded
- [ ] Live engine integration w/ real transactions
- [ ] Add investment return modeling logic
- [ ] Discrepancy analytics pipeline
- [ ] Validation & error boundaries for edge cases

---

## 📡 Forecast API Endpoints

### `GET /api/forecast/summary`

- **Query Params**:

  - `user_id`
  - `viewType`: `'Month' | 'Year'`
  - `manualIncome` (optional)
  - `liabilityRate` (optional)

- **Returns**: Labels, forecast\[], actuals\[], metadata

### `POST /api/forecast/calculate`

- **Body**:

  - `user_id`
  - `viewType`
  - `manualIncome`
  - `liabilityRate`

- **Returns**: Same format as `/summary`, supports advanced input configs

---

## ⚙️ Engine Architecture Summary

- **Data sources**: `accounts`, `recurring_transactions`, `account_history`, `transactions`
- **Vue composable**: `useForecastEngine.ts`
- **Output**: `forecastLine[]`, `actualLine[]`, `labels[]`
- Accepts both mock data and live integrations

---

## 🧱 Related Database Tables

- `accounts`
- `account_history`
- `recurring_transactions`
- `transactions`
- (Planned) `investments`

---

## 🚀 Pending Enhancements

- [ ] Ingest real transactions into forecast model
- [ ] Flatten recurring logic into daily/month aggregates
- [ ] Add investment growth input
- [ ] Store forecast snapshots (optional caching)
- [ ] CLI simulation utility
- [ ] Per-user forecast log/audit trail

---

## 🧪 Testing & Dev Utilities

- `ForecastMockPage.vue`: mock-driven UI testbed
- `ForecastLayout.vue`: main live-integrated consumer
- Composable accepts both `ref()` and static data
- Toggle between mock/live via simple flag
- Supports future backend switching during dev

---

_Module 3 of 3: Use this to track dev-phase implementation and future planning._

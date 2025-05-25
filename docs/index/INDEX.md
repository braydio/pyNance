
# 📊 pyNance Forecast Engine – Documentation Index

This repo implements a dynamic forecast engine that models projected vs. actual financial flows for each user. Below is the full documentation structure across backend logic, frontend components, API design, and ongoing dev planning.

---

## 📁 Forecast Engine Specification (Modular)

| Module | Description | Link |
|--------|-------------|------|
| **Module 1** | Architecture & Data Model – Input types, feature breakdown, actuals fallback | [Forecast Working Dir](#) |
| **Module 2** | Backend API & Integration – Live forecast calculation and Flask route strategy | [Forecast Working Dir](#) |
| **Module 3** | Development & Enhancement Tracker – Implementation checklist and dev-mode support | [Forecast Working Dir](#) |

> 🧠 These are internal design docs authored for development and referencing. This index should provide a list of currently active development processes.

---

## 📄 Supporting References (GitHub Markdown Files)

| File | Description |
|------|-------------|
| [`01REF_Architecture_Design.md`](https://github.com/braydio/pyNance/blob/main/frontend/src/components/forecast/01REF_Architecture_Design.md) | Engine logic flow, component roles, data formats |
| [`02REF_API_Integration.md`](https://github.com/braydio/pyNance/blob/main/frontend/src/components/forecast/02REF_API_Integration.md) | Backend route specs and implementation flow |
| [`03REF_Development_Planning.md`](https://github.com/braydio/pyNance/blob/main/frontend/src/components/forecast/03REF_Development_Planning.md) | Live integration planning, auth, date handling, endpoint testing |

---

## 📦 Forecast Components Directory

Forecast-related components live in:  
[`frontend/src/components/forecast/`](https://github.com/braydio/pyNance/tree/main/frontend/src/components/forecast/)

Key components:

- `ForecastChart.vue` – renders forecast vs actual lines
- `ForecastAdjustmentsForm.vue` – user override inputs
- `ForecastBreakdown.vue` – visual breakdown by category
- `ForecastLayout.vue` – page layout for embedding forecast views
- `ForecastSummaryPanel.vue` – summary stats display

---

## 🚀 Getting Started (Dev)

- Start from `ForecastComponent.vue`
- Mock testing via `ForecastMockPage.vue`
- Backend integration scaffolded in `routes/charts.py` (WIP)

For forecast logic, refer to `useForecastEngine.ts` under composables.

---

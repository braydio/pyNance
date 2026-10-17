# Expanded chart ranges (2026-10-17)

Shared historical presets in `frontend/src/composables/useDateRange.js`: 7D, 30D, MTD, 3M, 6M, YTD, 1Y; manual picker remains Custom. Intervals use **inclusive local dates** and a rolling calendar-month definition for 3M/6M/1Y, not UTC days. MTD/YTD start the current calendar month/year; no future dates.

Consumers: Dashboard overview (the same `dateRange` still drives Daily Net, summary, period counts, and category/merchant breakdown); standalone Cash Flow and Category chart routes; expanded Financial Summary; Accounts balance-history/activity (`ytd` now supported); future Forecast horizon offers 1M/3M/1Y (Quarter requests 90 days from `/api/forecast/compute`).

The dashboard's **Expand chart** navigates to `/charts/cashflow` retaining start/end query values. Category/merchant chart has its own expansion link and also retains dates and category/merchant mode. Non-time-based Allocation by Type remains a present-tense snapshot; Year Comparison retains side-by-side calendar years; YTD of a *future forecast* is not meaningful. Chart comparison overlay for longer selected ranges uses the preceding equal-duration interval.

Compatibility: `rolling_30` and `mtd` IDs remain; `custom` still labels manual dates; chart endpoints accept dates and update on prop changes, with no new external provider requests. Dashboard comparisons and future forecast calculations remain distinct (forecast horizon must not be bound to historical chart dates).

Suggested checks: `cd frontend && npm run test -- --run src/composables/useDateRangePresets.spec.js src/components/charts/__tests__/DailyNetChart.spec.js src/views/__tests__/Dashboard.spec.ts src/components/dashboard/__tests__/DashboardSections.spec.ts && npm run build`. Also manually verify YTD Jan 1 boundary, month-end/leap-year calendar clamping, missing history/empty state, and 390px toolbar wrapping.

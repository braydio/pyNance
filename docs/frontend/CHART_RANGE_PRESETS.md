# Expanded chart ranges (2026-10-17)

Shared historical presets in `frontend/src/composables/useDateRange.js`: 7D, 30D, MTD, 3M, 6M, YTD, 1Y; manual picker remains Custom. Intervals use **inclusive local dates** and a rolling calendar-month definition for 3M/6M/1Y, not UTC days. MTD/YTD start the current calendar month/year; no future dates.

Consumers: Dashboard overview (the same `dateRange` still drives Daily Net, summary, period counts, and category/merchant breakdown); standalone Cash Flow and Category chart routes; expanded Financial Summary; Accounts balance-history/activity (`ytd` now supported); future Forecast horizon offers 1M/3M/1Y (Quarter requests 90 days from `/api/forecast/compute`).

The dashboard's **Expand chart** navigates to `/charts/cashflow` retaining start/end query values. Category/merchant chart has its own expansion link and also retains dates and category/merchant mode. Non-time-based Allocation by Type remains a present-tense snapshot; Year Comparison retains side-by-side calendar years; YTD of a *future forecast* is not meaningful. Chart comparison overlay: MTD compares the same days of the prior month, YTD the prior calendar year to date, everything else the immediately preceding equal-duration interval (see [DAILY_NET_CHART.md](./DAILY_NET_CHART.md)).

Compatibility: `rolling_30` and `mtd` IDs remain; `custom` still labels manual dates; chart endpoints accept dates and update on prop changes, with no new external provider requests. Dashboard comparisons and future forecast calculations remain distinct (forecast horizon must not be bound to historical chart dates).

Suggested checks: `cd frontend && npm run test -- --run src/composables/useDateRangePresets.spec.js src/components/charts/__tests__/DailyNetChart.spec.js src/views/__tests__/Dashboard.spec.ts src/components/dashboard/__tests__/DashboardSections.spec.ts && npm run build`. Also manually verify YTD Jan 1 boundary, month-end/leap-year calendar clamping, missing history/empty state, and 390px toolbar wrapping.

## Daily Net bar granularity (TP-20261019-001)

The selected range always drives every dashboard widget; only the **bar bucket** of the Daily Net / Cash Flow chart changes. The mapping lives in `frontend/src/utils/dailyNetBuckets.js::resolveNetGranularity` and consumes `CHART_RANGE_PRESETS` / `getChartPresetRange` (no second preset table).

| Preset | Bucket | Ordinary bars |
| --- | --- | --- |
| 7D, 30D, MTD | local calendar day | 7, 30, 1–31 |
| 3M, 6M | Monday–Sunday week | ~13–15, ~26–28 |
| YTD | calendar month (Jan through current) | 1–12 |
| 1Y | calendar month | ~12–13 incl. partial ends |
| Custom | ≤45 days daily; 46–210 weekly; >210 monthly; >1095 quarterly | bounded |

Buckets are the intersection of the inclusive `[start, end]` and calendar periods, so the first/last weekly/monthly bar may be partial and shows its real inclusive dates. Weeks start Monday (not locale Sunday); quarters are calendar Q1–Q4. All day math uses UTC day numbers, so DST, leap day and year ends cannot add or drop a day. The range selector's "zoomed out" toggle coarsens the bucket one level (daily to weekly to monthly to quarterly) without fetching extra range.

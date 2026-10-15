# TP-20261014-015: Dashboard and Direct Chart Route Detail Polish

**Packet ID:** TP-20261014-015  
**Status:** Complete  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** docs/task-packets/completed/TP-20261014-015-dashboard-charts-standalone-pages.md  
**Depends on:** TP-20261014-010, TP-20261014-011, TP-20261014-012, TP-20261014-014  
**Priority:** High  
**Workstream size:** One focused UI packet  
**Source audit:** docs/frontend/UI_FIELD_AUDIT_2026-10-14.md

## Exact file paths
- frontend/src/views/Dashboard.vue
- frontend/src/views/FinancialSummaryDetailed.vue
- frontend/src/router/index.js
- frontend/src/components/dashboard/NetOverviewSection.vue
- frontend/src/components/dashboard/CategoryBreakdownSection.vue
- frontend/src/components/statistics/FinancialSummary.vue
- frontend/src/components/statistics/DailySpendingPanel.vue
- frontend/src/components/widgets/TopAccountSnapshot.vue
- frontend/src/components/charts/DailyNetChart.vue
- frontend/src/components/charts/CategoryBreakdownChart.vue
- frontend/src/components/charts/NetYearComparisonChart.vue

## Confirmed current state
Dashboard has chart controls, overlays, type switches, Financial detail disclosure, Snapshot group editing and account expansion. Category toolbar nested inside section heading; dropdown ancestor overflow-hidden. FinancialSummaryDetailed dateRange initializes {start:'',end:''}. /charts/cashflow and /charts/category router records mount chart components whose required date props aren't passed.

## Required implementation
Keep already-completed Dashboard hierarchy and logic; refine control spacing/contrast/active states, mobile wrap, secondary legends, detail headings, bounded long labels, expanded account groups, chart overlay priority. Initialize /summary MTD start/end via local YYYY-MM-DD and functional date range inputs. Wrap bare standalone cashflow/category routes in minimal page components supplying required dates/heading/loading/error and maintain same URLs, with year comparison toggle + empty state. Ensure chart and popover regions separately control overflow; no plot canvas toolbar clipping.

## Validation
Dashboard.spec.ts, DashboardSections.spec.ts, TopAccountSnapshotEditing.spec.js, DailyNetChart.spec.js + new chart-route mount tests. Browser /, /summary, /charts/cashflow, /charts/category, /charts/assets/year-comparison at 390/1280 light/dark with menu/detail expanded. lint/build.

## Non-goals
No duplicate TP-001..004 fixes; no new cashflow math.

## Completion contract
Check AGENTS.md and docs/task-packets/README.md, TRACKER and INDEX; validate named paths only. Mark In Progress, implement ordered fixes, run focused tests and lint/build. After completion move packet to completed/, update INDEX/TRACKER atomically, commit to origin/main without force. Report files, browser validation vs static assumptions, exact commands/output and deviations. Coordinate overlapping files with prerequisite packets; no broad refactor.

## Completion report

- Routes: `/charts/cashflow`, `/charts/category` and `/charts/assets/year-comparison` keep their paths and names but now render `views/ChartRoutePage.vue` (route `props.variant`), which supplies a heading (`PageHeader`), a month-to-date range with working `DateRangeSelector` inputs, the category dropdown/selection for the category chart, and the year comparison without a date picker. Bare chart components no longer mount without their required date props.
- `/summary` (`FinancialSummaryDetailed.vue`) now initializes month-to-date local `YYYY-MM-DD` dates instead of `{start:'',end:''}`.
- `NetYearComparisonChart.vue`: loading, empty ("No balance history yet...") and error-with-Retry states, `aria-pressed` + `type="button"` on the Assets/Liabilities/Net Worth toggles.
- Dashboard polish (no logic changes): meaningful small text raised to >= 0.8125rem in `NetOverviewSection`, `DailyNetChart` chips/legends, `ChartDetailsSidebar`, `CategoryBreakdownSection` and `DailySpendingPanel` (>= 0.75rem in the dense `TopAccountSnapshot`); helper text in `NetOverviewSection` uses `text-sm`; popover/chart overflow separation was done in TP-012 (only the chart region clips).
- **Bug found and fixed:** `composables/useDateRange.js` shadows `useDateRange.ts` (the bundler resolves `.js` first), so the `initialRange` option I added to the `.ts` file in TP-003 was never used and the Dashboard still defaulted to the end of the month. The `.js` file now has `initialRange` and `getMonthToDateRange` too (both files kept in sync), and a new unmocked `composables/__tests__/useDateRange.spec.js` covers it; `Dashboard.spec.ts` mocks this module, which hid the problem.
- Tests: new `views/__tests__/ChartRoutePage.spec.js` (props, dates, category wiring, route names/paths), `FinancialSummaryDetailed.spec.js`, year-comparison state tests, `useDateRange.spec.js`. Full vitest 65 files / 425 tests, lint 0 errors, build OK.
- Not run: browser checks of `/`, `/summary`, `/charts/*` at 390/1280 in both themes; `TopAccountSnapshotEditing.spec.js` is not present in the repo (the closest existing coverage ran as part of the suite).

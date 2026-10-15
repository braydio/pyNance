# TP-20261014-003: Dashboard Date Controls One Visible Period

**Packet ID:** TP-20261014-003  
**Status:** Ready  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** docs/task-packets/active/TP-20261014-003-dashboard-shared-period-truth.md  
**Workstream size:** One shared dashboard period-contract packet  
**Depends on:** None  
**Priority:** High  
**Source reviewed:** main @ 4ef24fd358e4d630108420e4bacc98ec5733d278  
**Series:** 3 of 4 (004 follows 003 on Dashboard/NetOverview files)

## Objective
Make a date selection mean what the UI suggests: Daily Net chart, Cash direction, Financial Snapshot, category breakdown, and review/browse count must describe one displayed reporting period. Safe-to-Spend remains an independent today/payday/week horizon explicitly labeled as such.

## Confirmed current seams
- frontend/src/views/Dashboard.vue: useDateRange() drives debouncedRange for category queries/review filters, but netRange is separately computed from netTimeframe (MTD or rolling 30 anchored to NOW). DateRangeSelector under Daily Net edits dateRange while DailyNetChart gets netRange. The visible date boxes do NOT govern the adjacent chart.
- frontend/src/components/dashboard/NetOverviewSection.vue: activeRange = netRange || debouncedRange; separate MTD/Rolling 30 buttons emit update:net-timeframe.
- frontend/src/components/charts/DailyNetChart.vue: timeframe is used to build prior-series comparison, not to determine the supplied display range; buildComparisonContext() assumes MTD or fixed 30 days.
- frontend/src/composables/useDateRange.ts defaults to month END (future days), whereas Dashboard netRange defaults to today.

## Required edits (in order)
1. Dashboard.vue: make debouncedRange the sole source for actual chart display boundaries (remove separately computed netRange). Initialize THIS dashboard's end to today's date, not future month end; leave shared useDateRange.ts defaults intact. Keep selectedPreset ref with values mtd|rolling_30|custom. Add setDashboardPeriodPreset(mode) that atomically sets dateRange.start/end (MTD: first-of-month through today; rolling_30: today minus 29 through today), selectedPreset and netTimeframe. Manual start/end edits set selectedPreset='custom'; the chart receives the new debouncedRange.
2. NetOverviewSection.vue: DateRangeSelector gets accessible "From"/"Through" labels (in frontend/src/components/DateRangeSelector.vue). Its change events go to Dashboard date setter; preset buttons become range presets, with a visible Custom state when manual dates differ. Show exact selected period near "Cash direction" and "Financial details" so "this period" is not ambiguous. Ensure MTD/rolling quick buttons and custom dates can't show conflicting active styles.
3. DailyNetChart.vue: extend timeframe validator to custom for optional comparison overlay. For custom prior-period comparison, use the immediately preceding calendar window of the SAME inclusive day count: days = 1 + (UTC(end)-UTC(start))/86400000; priorEnd=start-1 day; priorStart=priorEnd-(days-1). Update buildComparisonContext/buildComparisonSeries to use ctx.days instead of hard-coded 30 for non-MTD. Keep MTD day-aligned comparison and rolling_30 window of 30. Never imply custom uses previous MTD. Account for DST through UTC date keys.
4. Current header today-only Safe-to-Spend must not silently follow history controls. Mark it "Current guidance (not filtered by chart dates)" in concise help copy. Preserve TransactionModal date normalization and category/merchant drilldowns.

## Tests / validation
- frontend/src/views/__tests__/Dashboard.spec.ts; frontend/src/components/dashboard/__tests__/DashboardSections.spec.ts; frontend/src/components/charts/__tests__/DailyNetChart.spec.js; frontend/cypress/e2e/dashboard.cy.js if selectors exist.
- Cases: selecting 2025-01-08 to 2025-01-17 updates chart and category and counts to exactly those dates; MTD/rolling presets change both picker values AND chart query; custom prior-period is 10 days not 30, including month boundary; quick presets reset Custom; Safe-to-Spend horizon stays unchanged; fresh month default end=today.
- cd frontend && npm run test -- --run src/views/__tests__/Dashboard.spec.ts src/components/dashboard/__tests__/DashboardSections.spec.ts src/components/charts/__tests__/DailyNetChart.spec.js && npm run lint && npm run build

## Non-goals
Do not alter daily-net backend financial totals, forecasting engine, useDateRange on other pages, or global chart styles. Do not rediscover: exact paths and functions above.

## Acceptance / completion report
- [ ] Picker, chart, snapshot, and category show the same displayed period.
- [ ] Presets and manual dates never disagree; custom comparison has correct equal-duration baseline.
- [ ] Safe-to-Spend independence is obvious; existing chart click drilldown works.
Report query boundaries in tests, paths, commands/results, and any deviations.
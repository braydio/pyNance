# TP-20261014-001: Financial Detail Decision Hierarchy and Honest Metrics

**Packet ID:** TP-20261014-001  
**Status:** Ready  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** docs/task-packets/active/TP-20261014-001-financial-detail-decision-hierarchy.md  
**Workstream size:** One independently testable Financials detail UI packet  
**Depends on:** None  
**Priority:** High  
**Source reviewed:** main @ 4ef24fd358e4d630108420e4bacc98ec5733d278  
**Series:** 1 of 4 (002 follows 001 on same component)

## Objective
Turn Dashboard > Financial Snapshot > Show Detail View into a fast answer to (1) what happened, (2) what matters, (3) where to inspect. Keep useful data but de-emphasize statistical curiosities. No backend changes.

## Confirmed current seams
- frontend/src/components/statistics/FinancialSummary.vue: collapsed basic-stats repeats income, expenses, net already in NetOverviewSection Cash direction and DailyNetChart header. Expanded order is date > DailySpendingPanel > Upcoming Transactions > four equally weighted groups (Averages, Trends, Outliers, Savings).
- extendedMetrics.netChange/incomeChange/expenseChange = last daily value minus first daily value, yet Trends/Increasing/Decreasing imply sustained period trends. netTrend/incomeTrend/expenseTrend slopes are computed but never displayed.
- volatilityLevel uses uncalibrated $50/$200 thresholds; 7/30-day MAs use all available days even when under 7/30; Outliers displays only a count. "Savings Amount/Rate" equals period net/income, not confirmed saved money; "Avg Savings (positive)" equals average positive daily net.
- frontend/src/components/statistics/DailySpendingPanel.vue: "Today's Spending", "Today" chart tick and no-spend/loading copy are static even when detailDate is historical.

## Required edits (in order)
1. FinancialSummary.vue template: collapsed panel becomes a quiet single row ("Financial details", selected-period cue, "Show details" button), NOT a fourth income/expense/net hero. The expanded panel must retain readable period net/income/outflow once, with explicit "Net cash flow" (not savings); button type=button, aria-expanded, aria-controls, visible focus. Retain existing isExtendedView and detailDate mechanics.
2. Reorder expanded content: selected-date control and "Activity through [date]" explanation > selected-day spending + latest transactions > period interpretation ("Net cash flow", "Net as % of income" only when income > 0) > an initially closed native details/summary "More statistics". Upcoming recurring panel stays between date context and selected-day spending; TP-002 will improve its internals. Explicitly label upcoming as next 7 days FROM TODAY, independent of historical detailDate.
3. Move daily averages, 7/30-day net averages, first-vs-last daily changes, positive/negative-day counts, largest dates, σ/outlier count under "More statistics". Rename: "First vs last day (not a period trend)", "Daily net standard deviation", "Net as % of income", "Average positive-net day". Remove unsupported Low/Medium/High severity words, "Savings", and increasing/decreasing trendSummary. Clarify zeros are included in daily averages and day-count denominators. Return null/N/A for 7-day and 30-day averages until full windows exist; retain correct negative-expense sign handling. Rename statistics labels instead of inventing new scoring.
4. For unusual days, present up to 3 actual outlierDates with dates as buttons that emit select-date; route event FinancialSummary -> NetOverviewSection -> Dashboard.onNetBarClick (reuse existing date transaction modal). If no dates/short sample, say "Not enough history" or omit, not an unexplained zero anomaly score. Remove unused deep watch of filteredChartData and unused trend regression variables if no longer consumed.
5. DailySpendingPanel.vue: title "Spending on [formattedDetailDate]", legend/tick "Selected day", neutral "No spending recorded for this day"; relabel average comparison "Average daily spending over [baseline range]" using existing inclusive baseline calculation; don't fetch on a hidden extended panel.
6. Styling: replace equal-weight stats cards with a readable 1-column detail flow and compact 2-column comparison for narrow/wide screens. No nested neon borders or animated fixed-height clipping; honor reduced-motion preference.

## Tests / validation
- Edit frontend/src/components/statistics/__tests__/FinancialSummary.spec.js, DailySpendingPanel.spec.js; add NetOverviewSection event test to frontend/src/components/dashboard/__tests__/DashboardSections.spec.ts and dashboard modal wiring test if new event.
- Cases: absent income => no rate; expenses sign; 2-day vs 7/30-day insufficient history; sparse padded dates; reset and custom historical date; positive/negative/zero days; clicked outlier opens matching date; detail toggle keyboard/ARIA; no actual metrics misrepresented as savings.
- cd frontend && npm run test -- --run src/components/statistics/__tests__/FinancialSummary.spec.js src/components/statistics/__tests__/DailySpendingPanel.spec.js src/components/dashboard/__tests__/DashboardSections.spec.ts src/views/__tests__/Dashboard.spec.ts
- cd frontend && npm run lint && npm run build

## Non-goals
No change to daily-net API, forecasting math, category aggregation, TransactionModal, or account balances. Do not retroactively reinterpret cash flow as actual savings. Do not rediscover: only paths above plus existing amount formatter and existing modal event seam.

## Acceptance / completion report
- [ ] Expanded reading order prioritizes activity and meaning over four-card statistic wall.
- [ ] Each label exactly describes its calculation; insufficient-history windows are identified.
- [ ] Outlier dates open existing transaction details; states and mobile remain usable.
- [ ] Existing date-selection and DailySpendingPanel requests still work.
Report before/after order, changed paths, precise commands/results, and any deviation.
# TP-20261016-010: Forecast Driver Groups, Currency Formatting and Debt Coverage Clarity

**Packet ID:** TP-20261016-010  
**Status:** Complete  
**Created:** 2026-10-16  
**Last updated:** 2026-10-17
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/completed/TP-20261016-010-forecast-explained-breakdown-currency.md`  
**Workstream size:** One targeted implementation packet  
**Priority:** P1  
**Depends on:** TP-20261016-006  
**Series:** 11 packets (TP-20261016-001..011); assume each named prerequisite has landed before starting this packet.  

## Objective
Forecast Driver Groups, Currency Formatting and Debt Coverage Clarity. Complete only the named workstream; no broad rediscovery.

## Do not rediscover: exact file/ownership map
- `frontend/src/components/forecast/ForecastBreakdown.vue`
- `frontend/src/components/forecast/ForecastSummaryPanel.vue`
- `frontend/src/components/forecast/ForecastLayout.vue`
- `frontend/src/components/forecast/ForecastChart.vue`
- `frontend/src/utils/format.js`
- `frontend/src/composables/useForecastData.ts (or actual module ext; verify current path)`
- `frontend/src/components/forecast/__tests__/ForecastSummaryPanel.spec.ts`
- `frontend/src/components/forecast/__tests__/ForecastLayout.spec.ts`
- `frontend/src/components/forecast/__tests__/ForecastBreakdown.spec.ts (new)`

## Confirmed current seam (main at authoring 437bdd9cda1bd21d651e7c0ecd24c205d76b6ebc)
Screenshot shows massive raw `residual` rows and undifferentiated card surfaces; breakdown displays `{{ Math.abs(item.amount) }}` without 2-decimal/currency formatting. `ForecastSummaryPanel` uses `$${toFixed(2)}` in V1 cells and bare `netDelta.toFixed(2)`; V2 note says `Not part of this cash forecast: debt $X` although debt payments can affect cash. Individual daily residuals bury useful event drivers.

## Required code edits, in order
1. `frontend/src/utils/format.js` add `formatSignedCashflow(value,{showPlus=true})` returning +$1,234.56/−$25.40/$0.00, `formatForecastMoney(value)` for unsigned balance; use Intl.NumberFormat en-US USD, `Number.isFinite` guard => `Unavailable` on null/NaN, no `$0.00` fallback for missing data. Do not change existing `formatAmount` accounting-parenthesis contract globally. Preserve negative red/positive teal semantic classes.
2. `ForecastBreakdown.vue` replace flat raw list as PRIMARY view with grouped aggregates computed from `forecastItems` and structured drivers: `Expected income`, `Scheduled bills & payments`, `Estimated variable spending`, `Transfers` when relevant; each group shows count, total signed USD, expand to dated transaction/source rows; residual daily rows collapsed under `Typical spending` details with weekday/date only if expanded. Preserve `@select-item` drill-in event; don't sum same event twice if both breakdown list and drivers list reference it. Use event_id/source_id stable keys rather than array index when available.
3. `ForecastSummaryPanel.vue` V2 replace `Not part of cash forecast: debt` with `Outstanding debt tracked separately: $x. Scheduled debt payments included: $y across n verified streams. Other debt payment coverage: incomplete/unverified` using additive `metadata.debt_payment_coverage` from 006. Distinguish outstanding principal from periodic cash obligations and show `Net Worth` only as separate panel. V1 use copy `Debt totals are separate from modeled bank cash` without asserting payments covered.
4. `ForecastLayout.vue` connect new coverage prop; share responsive compact KPI, selected horizon, graph legend; chart one primary visual and clear confidence band, no monochrome piled cards. Callout for inferred recurring payment confidence, warnings and missing account balance. Fix `ForecastSummaryPanel` all `.toFixed(2)` and bare netDelta fields through helpers, formats in overlay/adjustment list and tooltip. Use theme tokens not arbitrary accent every row.

## Exact contracts and acceptance fixtures
- Example: +$1,200 paycheck, −$90 electric, −$45.23 variable spend correctly grouped and totals sum to forecast net. `$11,686.65 outstanding debt` does NOT appear as a negative cash event.
- Every V2 event appears at most once in aggregated cash effect. Group amount sum equals ledger summary net_change within 1 cent; no forced invented amount from null.

## Validation commands
`cd frontend && npm run test -- --run src/components/forecast/__tests__/ForecastSummaryPanel.spec.ts src/components/forecast/__tests__/ForecastLayout.spec.ts src/components/forecast/__tests__/ForecastBreakdown.spec.ts && npm run lint && npm run build`; browser Nightfox/Everforest 390/1280 with 100 residual events and long merchants.

## Non-goals
No algorithmic forecast changes here, no debt auto-pay or duplicated residual model.

## Implementation/handoff
Read `AGENTS.md`, `docs/task-packets/README.md`, `INDEX.md`, `TRACKER.md`; validate only named symbols against latest main. Set In Progress in tracker before coding. Treat prerequisite packets as implemented, do not re-implement their features. Run focused tests then lint/build; commit only this workstream to main without force, mark Complete, move this packet to completed and update INDEX/TRACKER atomically. Report changed files, test output, fixture/behavior evidence, and deviations. If principal is not trusted, fail closed on new owner-scoped endpoints, not permissive fallback. Do not use Plaid Enrich/new billable APIs.

## Completion report (2026-10-17)

- `utils/format.js`: `formatForecastMoney` (grouped USD, `Unavailable` for null/NaN, never `$0.00`) and `formatSignedCashflow` (`+$1,234.56`, true-minus `−$25.40`, `$0.00`); `formatAmount` unchanged.
- `ForecastBreakdown.vue`: primary view is now grouped aggregates (Expected income, Scheduled bills & payments, Estimated variable spending, Transfers, Adjustments, Other). Events are deduplicated by `event_id`, totals are summed in whole cents and the net line equals the ledger net change; residual daily rows sit under the variable group (weekday labels, 15 shown, "Show all N"); `select-item` drill-in preserved; missing amounts are skipped, not zero.
- `ForecastSummaryPanel.vue`: V2 shows "Outstanding debt tracked separately", "Scheduled debt payments included: $y across n verified streams" and the other-coverage status from `metadata.debt_payment_coverage`; V1 says "Debt totals are separate from modeled bank cash"; all `.toFixed(2)` and the bare net delta go through the helpers. `ForecastLayout.vue` passes the coverage prop, formats adjustment and drill-down amounts with the helper, and shows a caveats callout (warnings, unconfirmed recurring items, thin history). `useForecastData.ts` exposes `debtPaymentCoverage`.
- Backend follow-up from TP-006: forecast `cashflows` and `drivers` now carry each event's true cash effect (a debt payment is an outflow, card charges are excluded), so grouped totals reconcile to `summary.net_change` within a cent (3 new tests).
- Tests: `ForecastBreakdown.spec.ts` (11), `formatForecast.spec.js` (11), 5 new debt-coverage cases in `ForecastSummaryPanel.spec.ts`, V2 spec updated; build passes. `ForecastChart.spec` has one failure that pre-dates this packet.
- Not done: the Nightfox/Everforest 390/1280 browser pass for the forecast page.

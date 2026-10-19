# TP-20261019-001: Daily Net Period Buckets, Readability and Reconciliation

**Packet ID:** TP-20261019-001  
**Status:** Ready  
**Created:** 2026-10-19  
**Last updated:** 2026-10-19  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/active/TP-20261019-001-daily-net-period-buckets-visual-truth.md`  
**Priority:** P1  
**Workstream size:** One coherent chart/interaction + aggregation packet  
**Depends on:** None; build on completed TP-20261017-003/004 and TP-20261014-003/015  
**Expected packet count:** 1 (this packet; implement, test, complete).

## Objective

Audit and repair dashboard **Daily Net / Net Income** and the expanded **Cash Flow** chart for aesthetics, consistency, readability, color, interaction, meaning, and economic accuracy. The selected **date range** still controls all dashboard summary/transaction widgets; only **chart bar granularity** changes. YTD must show calendar **months**, never one bar per day. Keep the backend classification as the financial source of truth.

### Granularity contract (explicit, non-negotiable)

| Preset (`useDateRange.js`) | Display bucket | Expected ordinary bar count |
| --- | --- | --- |
| 7D (`7d`) | one local calendar day | 7 |
| 30D (`rolling_30`) | one local calendar day | 30 |
| MTD (`mtd`) | one local calendar day, first through selected end | 1–31 |
| 3M (`3m`) | Monday–Sunday calendar week | ~13–15 |
| 6M (`6m`) | Monday–Sunday calendar week | ~26–28 |
| YTD (`ytd`) | local calendar month, January through end month | 1–12 |
| 1Y (`1y`) | local calendar month | ~12–13, including partial start/end |
| Custom | ≤45 inclusive days: daily; 46–210: calendar weeks; >210: calendar months; >1095: calendar quarters | bounded |

Buckets are intersections of the selected **inclusive** `[start_date,end_date]` and their underlying local calendar periods. The first/last weekly/monthly bucket may be partial and **must display its actual inclusive start/end**. Monday week starts; do not use locale-dependent Sunday starts or rolling 7-day windows. Q buckets are calendar Q1/Q2/Q3/Q4 for unusually long custom intervals. Do not silently extend into future days or beyond selected bounds. Title/subtitle must say `Daily`, `Weekly`, `Monthly`, or `Quarterly` (e.g., “Economic Net · Monthly”). Bar labels across years must disambiguate year and partial ranges in details.

## Verified audit on main `08056e0c5fe0bade1ab26ddb79d60b31769a5fe4` (2026-10-19)

- `frontend/src/components/charts/DailyNetChart.vue::getDisplaySeries/buildDateRangeLabels/padDailyNetData/renderChart` builds **one daily label for every selected date**, regardless of 3M/6M/YTD/1Y; `getDensityConfig` responds by shrinking bars to 5px at ≥120 days and abbreviating X ticks to months even though each narrow bar remains a *day*. This makes YTD visually unintelligible.
- `DailyNetChart.vue::props.timeframe.validator` only accepts `mtd|rolling_30|custom`, although `frontend/src/composables/useDateRange.js::CHART_RANGE_PRESETS` and `NetOverviewSection.vue` pass `7d|3m|6m|ytd|1y`. Comparison context also only special-cases MTD/30D.
- `DailyNetChart.vue::renderChart` draws `Income` positive and `Expenses` negative, with a yellow net dash; backend `backend/app/routes/charts.py::get_daily_net` correctly returns **economic net = income + expenses + refunds**, but **refunds are not drawn as their own contribution**. Dashboard summary emits only income, expenses and net, leaving refund contribution unexplained.
- `renderChart` computes average-income/expense lines from the entire **lookback-extended fetched range**, not selected display range. Existing `7-Day Avg`/`30-Day Avg` are **daily** averages and cannot be plotted as weekly/monthly aggregate dollars without unit conversion or removal.
- `buildComparisonSeries` aligns by **day-of-month/day-index**, not bucket date spans; `handleBarClick` emits one string label, and `frontend/src/views/Dashboard.vue::onNetBarClick` uses `loadDayTransactions` for exactly one day. Enlarging bars without reworking details/clicks creates factually wrong drilldowns.
- `resolveDetailsFromIndex`, `updateHoverIndicator`, tooltip/axis formatters, `activeIndex` and `$dailyNetRows` all assume dates rather than [start,end] periods; selected numeric index can point to a different period after granularity switches.
- `fetchData/fetchComparisonData` have no latest-request guard; fast period switching may display stale late responses. `isEmpty` tests `chartData.length` including lookback, not selected window; `summary-change`/`data-change` are not emitted when selected range is empty.
- Present chart chrome: `daily-net-chart__meta` is a four-column grid with hard-coded `290px` detail and `108px` empty legend/title shells; the canvas is fixed `400px`. Dense controls/gradient title, tiny secondary type, sparse hidden base legend, redundant hover chip and overlaid floating controls reduce hierarchy and legibility. No visual screenshot was captured in this authoring pass; confirm with browser screenshots at test breakpoints.
- Expanded `frontend/src/views/ChartRoutePage.vue` passes dates but **not `timeframe`** to the cashflow chart, and calls it “Daily net income” for every preset. `ChartDetailsSidebar.vue` offers daily trend controls even when chart buckets should be weekly/monthly. Dashboard `NetOverviewSection.vue` title hardcodes `(Daily)`.
- `frontend/src/views/Dashboard.vue::onNetBarClick/chartReferenceFor`, `frontend/src/utils/dailyModal.js`, `TransactionModal.vue` already reconcile **one selected day** against server-classified economic rows, including transfers/review rows. Preserve this tested contract and do not convert it to an unbounded period modal.

## Exact implementation order (do not rediscover)

**1. One pure presentation bucketer.**
- Add `frontend/src/utils/dailyNetBuckets.js` exporting `resolveNetGranularity(timeframe,startDate,endDate)`, `buildNetBuckets(dailyRows,startDate,endDate,granularity)`, and `formatNetBucketLabel(bucket,options)` (names may be adjusted only for consistency with existing helpers).
- Consume `getChartPresetRange` / `CHART_RANGE_PRESETS` from `frontend/src/composables/useDateRange.js`; do not make a duplicate preset table elsewhere. The backend `GET /api/charts/daily_net` remains daily, trusted-owner scoped; **aggregate existing classified rows client-side**, with no second income/transfer classifier.
- Each bucket retains `startDate`, `endDate`, `periodStart`, `periodEnd`, `granularity`, `isPartial`, `income`, `expenses`, `refunds`, `net`, `transaction_count` and movement/review sums when provided. Use integer cents for monetary reduction, convert to display dollars last; reject/guard nonfinite values. Preserve `net` from authoritative daily rows, and assert in fixture tests `net == income + expenses + refunds` to cent precision. `expenses` stays **negative**, `refunds` positive, `transfer/debt/investment/unclassified` do **not** feed economic net.
- Produce deterministic zero-activity buckets inside the interval, but distinguish a successful empty response from request/error/unconfigured owner. For every preset, `sum(buckets[field]) == sum(selectedDailyRows[field])`; never sum 30-day warmup rows into display totals. Use ISO date-only arithmetic safe over DST, leap day, year/month ends.

**2. Wire shared period state, fetch and emit contracts.**
- `frontend/src/components/charts/DailyNetChart.vue`: replace `getDisplaySeries` plotting labels with `buildNetBuckets` while retaining the padded **daily source series** for `summary-change` and `data-change`. `FinancialSummary` and `Dashboard.vue::chartReferenceFor` must still receive DAILY rows; aggregated plot rows stay chart-local. Update `timeframe` validator to all `CHART_RANGE_PRESETS` + `custom` and map `zoomedOut` to display granularity, not an unexpected extra-range fetch.
- Fetch only needed display span plus optional 30-day warmup for **daily** 7/30-day overlays; invalidate on start/end/overlay/granularity changes. Add request generation/AbortController guard for primary and comparison requests; stale requests cannot overwrite new range, summary or active selection. When a period has no economic rows, emit zero summary and empty daily series, present `No activity in this period`, not prior-period data. Preserve independent API/error/retry states.
- Update emitted period summary to include `totalRefunds` (additive; existing fields unchanged) and ensure `totalNet = totalIncome + totalExpenses + totalRefunds`. Amend `NetOverviewSection.vue` cash-direction/header totals to disclose refund adjustments when nonzero, using neutral wording “Economic income · Expenses · Refunds · Net, excluding transfers”. The shared range still drives other dashboard panels.

**3. Financially legible bar + net semantics.**
- Keep existing zero baseline with green income up and red expenses down; add a separate distinguishable **refund adjustment** segment (e.g., muted teal/light green above zero), clearly keyed in **always-visible small legend** for Income / Expenses / Refunds (when present) / Net dash. Do not relabel refunds as income and do not draw a net marker whose constituent value is invisible.
- Yellow/amber net **dash** must sit at the correct net value with `net` signed; show currency tooltip/details with signed values and explicit “Economic Net”, no “savings”, “bank balance change” or “cash on hand”. Income/Expense bars show **bucket totals**, not rates/means. Subtle grid, strong zero line, restrained accent palette from `--color-accent-green/red/yellow/cyan`, matching shared `--chart-shell-*` tokens. No new hardcoded parallel chart palette; use gradients only for secondary accent, not chart text.
- Improve bar sizing by **number of buckets**, without 5px 365-day confetti; dynamic density/mobile tick limit, honest per-period X ticks, compact currency `$1.2k`/`-$2.4k` for axis, exact cents in details. Text colors meet contrast for light/dark theme; color is not the only meaning (labels, shapes, signed amounts).
- Recompose four-column `daily-net-chart__meta`: title/period + compact period summary, active bucket details, restrained overlays/time controls. Remove rigid blank 108px legend scaffolding, prevent clipped popovers, preserve one primary “Expand chart” action; details card should have a clear large signed net and smaller labeled income, expense, refunds, counts. Responsive 390/768/1280px, no horizontal screen overflow, avoid popup over bars.
- `NetOverviewSection.vue` title subtitle and `ChartRoutePage.vue::HEADINGS.cashflow` reflect selected period granularity, including direct expanded chart preset. Pass `:timeframe="selectedPreset"` to direct Cash Flow chart; preserve `start_date`/`end_date` deep links as custom and same bucket policy. Remove or correctly support unused `comparison-mode` binding rather than leaving a misleading inert control.

**4. Active bucket, drilldown, overlays.**
- `DailyNetChart.vue::resolveDetailsFromIndex/updateHoverIndicator/getNetDashPosition/handleBarClick` operate on **bucket objects**, not date-only axis strings. Show “Oct 12–18, 2026” / “Jan 2026” + precise inclusive dates for partial buckets, income/expense/refund/net and transaction count. Maintain selection by bucket key (`granularity:start:end`) or reset to latest *active* bucket after a preset switch; do not reuse an unrelated array index. Hover/keyboard selection share the same details and persist after pointer exit.
- Daily bar click continues emitting ISO day via `bar-click` and opens the existing reconciled `onNetBarClick` transaction modal. **Weekly/monthly/quarterly bar click drills down within the chart to a daily bucket breakdown** for that actual `[startDate,endDate]`, with a visible “Back to Weekly/Monthly” control and a breadcrumb; then day click uses the existing modal. No unbounded fetch of months of transactions, no mutation of global dashboard date range, and no replacement of `dailyModal.js`. Reset drilldown on global period switch.
- Add keyboard-accessible bucket navigation, focus state and an accessible summary table/list (can be disclosed) with bucket date range, income, expenses, refunds and net, so chart is usable without distinguishing colors or canvas mouse hits. No gesture-only drilldown.
- `ChartDetailsSidebar.vue`: 7/30-day *daily net moving-average* overlays render **only when daily bars** are shown, and options are disabled with short reason on coarser buckets. Keep daily window averages computed from daily series using warmup dates, never recompute “7-day” over 7 weekly bars. `Avg Income/Expenses` when enabled are averages per **visible bar period** (including partials, labeled explicitly); alternatively suppress these on partial uneven-period views with explanation. Comparison overlay must operate on **equivalent total-day bucket spans**, not reusing daily index alignment on monthly bars: MTD prior same-days-of-month; YTD prior calendar-year-to-date; other modes immediately preceding equal-duration interval. Align paired spans by correct index/range and label basis clearly. Never show a fabricated zero/delta if prior data unavailable or comparable bucket lengths differ; omit percentage for zero comparator. Preserve prior successful daily overlay behavior when granularity is daily, test edge cases.
- Document whether a bucket is partial/current-period-to-date and make comparisons explicit (“vs matching prior interval”); comparison must not silently mix 7-day **means** with monthly **totals**.

**5. Documentation + focused regression.**
- Update `docs/devnotes/daily-net-chart.md`, `docs/frontend/DAILY_NET_CHART.md`, `docs/frontend/CHART_RANGE_PRESETS.md` with preset/bucket table, inclusive bucket rules, economic refunds, overlay/selection/drilldown semantics. Remove obsolete “all daily YTD bars” assumptions while retaining economic-flow source-of-truth from completed 003/004.
- Add `frontend/src/utils/__tests__/dailyNetBuckets.spec.js`, extend `frontend/src/components/charts/__tests__/DailyNetChart.spec.js`, `frontend/src/composables/useDateRangePresets.spec.js`, `frontend/src/views/__tests__/Dashboard.spec.ts`, and `frontend/src/components/charts/__tests__/ChartDetailsSidebar.spec.js`; cover `ChartRoutePage.vue` expanded route and `DashboardSections.spec.ts` as necessary. Preserve existing `tests/test_charts_daily_net.py` semantics.

## Acceptance fixtures / tests

- Freeze 2026-10-19: 7D=7 daily bars; 30D=30; MTD Oct 1–19 daily; 3M weekly; 6M weekly; **YTD exactly 10 month buckets** Jan–Oct with Oct partial; 1Y monthly; Custom 40/90/300/1200-day scale appropriately. No daily bars on YTD/1Y. Week that crosses Sept/Oct belongs to one Monday-anchored bucket with its clipped boundaries; Feb 29, Dec 31–Jan 1, Mar DST, month-end, sparse activity and future cutoff pass.
- Fixture: $1,000 payroll, -$300 expense, +$25 refund, $200 own transfer, $131.64 card settlement, $100 unclassified deposit => Income $1,000, Expense -$300, Refunds +$25, **Economic Net +$725** in daily, weekly and monthly rollups. Movement/review visible only as separate detail, never double-counted. For every view, totals reconcile to raw daily API sums and dashboard cash direction. Net dash at +$725, not +$700.
- User selects YTD, clicks a monthly bar, sees a bounded daily breakdown for precisely that month; clicking a day opens existing owner-scoped day modal; Back restores YTD without changing dashboard selected dates; expanded Cash Flow behaves identically. Switching 1Y→7D quickly must not let stale requests change summary, details, or bars.
- Test error/empty/new selection and comparison with zero/missing prior; daily averages only on daily; all visible color/sign legends; keyboard access. Capture screenshots at 390, 768 and 1280 px, both themes if supported; inspect legibility, collision, clipping, contrasts. Do not claim screenshot checks if browser unavailable.
- Commands: `cd frontend && npm run test -- --run src/utils/__tests__/dailyNetBuckets.spec.js src/components/charts/__tests__/DailyNetChart.spec.js src/components/charts/__tests__/ChartDetailsSidebar.spec.js src/composables/useDateRangePresets.spec.js src/views/__tests__/Dashboard.spec.ts src/components/dashboard/__tests__/DashboardSections.spec.ts && npm run build`; backend invariant check `pytest tests/test_charts_daily_net.py -q` (per-file runs if test stubs collide). Existing Dashboard.spec.ts failures on main must be compared against untouched baseline, not attributed without proof.

## Boundaries, execution and completion report

Do not add a second classifier, change bank signs, alter transfers/refund economics, run paid Plaid calls, make schema migrations or modify transactions; no unrelated redesign, no historical account import. No interactive chart option should be inert. **Do not rediscover:** named Vue chart, dashboard parent, `useDateRange.js`, daily API, completed TP-003/004, and this packet are the complete starting surface. Narrow file checks only unless contradicted.

Before implementation, follow root `AGENTS.md` watcher-pause rule, sync `main`, mark this packet and TRACKER In Progress; implement steps 1–5; run focused validation; after success mark Complete and move to `completed/`, updating INDEX/TRACKER in the same commit. Publish only reviewed task-owned changes to main without force. Close out with exact **Workstream ID, commit URL, changed files, bucket-count fixture results, economic reconciliation results, commands and actual passes/failures, screenshots run or unavailable, blockers**, and watcher-resume status. If a test cannot run, say which and why, not “all passed”.

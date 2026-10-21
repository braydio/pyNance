# Daily Net Chart Design

This component renders a daily summary of income and expenses using stacked bars with a net line overlay. To emphasize cash flow, expense values are stored as negatives so that red bars extend **below** the X‑axis while green income bars remain above it.

The chart draws **period buckets**, not always days: daily for 7D/30D/MTD, Monday weeks for 3M/6M, months for YTD/1Y, with custom ranges scaling by length (see [CHART_RANGE_PRESETS.md](./CHART_RANGE_PRESETS.md) for the table). Buckets never extend past the selected inclusive `[start, end]`; the first/last bar may be partial and says so. The title reads "Economic Net · Daily|Weekly|Monthly|Quarterly". Periods without activity are zero bars; a period with no rows at all shows "No activity in this period" and emits a zero summary and empty series.

The title block shows compact period totals. When the period has refunds the wording is "Economic income · Expenses · Refunds · Net, excluding transfers" so the refund adjustment is never hidden.

Emitted data stays **daily**: `summary-change` carries `{totalIncome, totalExpenses, totalRefunds, totalNet}` (`totalNet = income + expenses + refunds`) and `data-change` carries the zero-padded daily rows for the selected period only (never the 30-day warmup). Aggregated bars are chart-local, so `FinancialSummary` and `Dashboard.vue::chartReferenceFor` keep reconciling one day at a time.

### Bars, net marker and legend

- Expenses (red, negative) and income (green) share a stack; **refunds** are their own teal segment stacked above income. Refunds are never relabelled as income.
- The yellow dash is the signed **Economic Net** (income + expenses + refunds) and is as wide as its bar. Transfers, debt settlement, investment movement and unclassified cash are *not* part of it.
- A small always-visible legend names Income, Expenses, Refunds (when present) and Economic net; overlay chips follow it.
- Axis values are compact (`$1.2k`, `-$2.4k`); the details panel shows exact cents. Bar width follows the bucket count (no 5px daily confetti), tick count is capped per viewport, and the zero line is emphasised.

### Selection and drilldown

- The active bucket is tracked by key (`granularity:start:end`); hover, click and keyboard share it, and it persists after the pointer leaves. After a period change it resets to the latest active bucket instead of reusing an array index.
- Daily bar click emits `bar-click` with the ISO day (parent opens the existing owner-scoped day modal, `dailyModal.js`). Weekly/monthly/quarterly bar click **drills into that bucket's days inside the chart** using already-fetched rows, with a "Back to Monthly" button and breadcrumb; Escape also goes back. Drilldown never changes the global dashboard dates and resets when the period changes.
- The canvas wrapper is focusable: ArrowLeft/Right, Home/End move, Enter drills or opens the day, Escape leaves a drilldown. A disclosed table lists every bucket's range, income, expenses, refunds and net with the same actions, so the chart is usable without the canvas or colour.

The chart emits a `bar-click` event with the associated date whenever a daily bar is activated. See [DASHBOARD_MODAL_GUIDE.md](./DASHBOARD_MODAL_GUIDE.md) for how these events open the transaction modal.

## Comparison Overlay

The dashboard overlay sidebar supports a comparison series that fetches a prior interval from
`/api/charts/daily_net` (`resolveComparisonInterval`) and pairs each bucket with the net of the **same day span** inside it (`buildComparisonNets`), so monthly bars compare to monthly totals, never to a mean:

- **MTD** compares the same days of the prior month ("This Day Last Month").
- **YTD** compares the prior calendar year to date ("Same period last year").
- **Everything else** compares the immediately preceding interval of equal inclusive length ("Previous period").

A bucket whose span runs past the prior interval gets no comparison value (no fabricated zero or delta), and the percentage is omitted for a zero comparator. A failed comparison request shows a notice and drops only the overlay; it does not blank the chart.

### Other overlays

- **7/30-day trends** are windows over *daily* net, drawn only on daily bars (and in a drilldown). On coarser buckets the sidebar disables them with a reason; they are never recomputed over weekly/monthly bars.
- **Avg Income / Avg Expenses** are the mean of the visible bar totals, labelled per bar period ("Avg Income / month (incl. partial)" when a partial bucket is included).

The comparison series renders as a faint, dashed line so it is visible without overpowering the primary
income and expense bars. Active overlays render as chips under the base legend and wrap instead of scrolling.

## Details Panel Behavior

The chart disables the built-in Chart.js tooltip (`plugins.tooltip.enabled = false`) and renders a persistent
details panel directly above the canvas so metric context remains visible without occluding bars/lines.

The panel tracks the active bucket (initially the latest bucket with activity) and uses index-based hover
(`mode: index`, `axis: x`, `intersect: false`) so details follow the hovered bar.

Panel hierarchy:

- Header: the bucket's inclusive dates ("Oct 12–18, 2026", "Feb 2026", with a "partial period" tag).
- Primary metric: signed **Economic Net**, coloured and signed so colour is not the only cue.
- Secondary metrics: Income, Expenses, Refunds, Transactions.
- Conditional comparison block: prior value + `vs prior` delta + percent when calculable.

## Loading, Empty, and Error States

The chart now manages explicit request/UI state with local reactive flags:

- `isLoading`: shows an inline loading state while primary or comparison requests are in flight.
- `isEmpty`: displays "No activity in this period" when no rows fall inside the selected window (warmup rows do not count). The title/toolbar slots stay mounted so the period can still be changed.
- `hasError`: shows an error banner with a retry action when either API request fails or returns a non-success status.

When `hasError` or `isEmpty` is active, chart rendering is deferred and the canvas/legend are hidden to avoid stale visuals. Primary and comparison requests carry a generation guard, so a late response from a previous period can never overwrite the current bars, summary or selection.

## Economic activity vs cash movement (TP-20261017-004)

The chart's `income`, `expenses` and `net` are **economic**: income + expenses + refunds as classified by `transaction_flow_classification`. Own-account transfers, card/loan payments, investment deposits and unresolved credits are cash movement and never count as income. The same buckets expose `transfer_in/out`, `debt_settlement`, `investment_movement` and `unclassified_*` so a day's bank movement can be reconciled. Labels read "Economic Net"; never "savings", "bank balance change" or "cash on hand".


## Cash movement vs economic activity (TP-20261020-001)

`GET /api/charts/daily_net` now carries two separate measures per day. Never add them together.

| Measure | Fields | Meaning |
| --- | --- | --- |
| Economic activity | `income`, `expenses` (negative), `refunds`, `net` | Purchase-time view. A later card or loan payment is not a second expense. Unchanged. |
| Cash movement (new, additive) | `cash_flow.money_out`, `money_in`, `net_cash` (USD, positive magnitudes; `net_cash = money_in - money_out`) | Actual posted movement of the owner's funding (depository) accounts. |

Money Out components: `direct_payment_out`, `debt_payment_out` (card and loan payments), `investment_allocation_out`, `external_person_out` (P2P wording), `unclassified_out` ("Needs classification"). Money In components: `income_in`, `refund_in`, `financing_in` (loan proceeds, never income), `investment_in`, `unclassified_in`. `verified_own_transfer_out/in` are reported but excluded from both totals.

Rules: only depository legs fund cash movement; card, loan and investment account legs are the other side of the same event and are not counted again. A verified transfer whose counterpart is a card or loan is a debt payment; to an investment account it is an investment allocation; between two cash accounts it is excluded. A transfer flagged `is_internal` with no verified pair stays in `unclassified_*` and is counted in `coverage.cash_flow.unverified_internal`.

`coverage.cash_flow` reports `funding_account_count`, `funding_leg_count`, `non_funding_leg_count`, `complete` (false when no cash account contributed, so the UI shows an incomplete state rather than a fabricated 0) and `needs_review`. Hidden accounts, pending rows and other owners are never loaded.

`GET /api/charts/cash_flow_diagnostic?start_date&end_date` (owner-bound, read only) explains why Money Out differs from economic expenses: counts and amounts by component, excluded non-funding legs, internal flags without a pair, and per-account, per-month totals. It returns no merchant names, memos or transaction ids.

UI: `DailyNetChart` takes `basis` (`economic` default, `cash`). The dashboard and chart route default to **Cash Movement** with an explicit **Economic Activity** toggle; the first viewport shows "Money out $X" with what it includes. Bucketing, zoom and day drilldown are unchanged.

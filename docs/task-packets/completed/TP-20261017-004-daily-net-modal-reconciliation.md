# TP-20261017-004: Reconcile Daily Net Chart and Transaction Modal

**Packet ID:** TP-20261017-004  
**Status:** Complete  
**Created:** 2026-10-17  
**Last updated:** 2026-10-18  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/completed/TP-20261017-004-daily-net-modal-reconciliation.md`  
**Priority:** P1  
**Workstream size:** One dashboard presentation / contract-validation packet  
**Depends on:** TP-20261017-003, TP-20261016-009  
**Series:** Follow-on 2/2; no second client-side economic classifier.

## Objective
Make Daily Net chart and clicked-day transaction modal agree on **economic** Income / Expense / Net, while preserving visible transfers and unresolved entries with separate subtotals and easy review. Do not simply hide transfer rows to make math match.

## Verified seams on main db9731b556c9823d407d147beb8238df169c5acd
- `frontend/src/components/modals/TransactionModal.vue::summary`: `Number(tx.amount) < 0 ? expense += amt : income += amt` regardless of transfer/category/owner; screenshot shows $300 as income from two movement-like credits.
- `frontend/src/views/Dashboard.vue::onNetBarClick` calls `fetchTransactionsApi({start_date,end_date,page:1,page_size:1000})`, loads modal rows separately from the Daily Net series; no aggregation reconciliation or >1000 warning.
- `frontend/src/components/tables/ModalTransactionsDisplay.vue` colors rows by sign alone and does not show flow category/transfer status. Chart `frontend/src/components/charts/DailyNetChart.vue` reads `income/expenses/net` from `GET /api/charts/daily_net`.
- API rows from `account_logic.get_paginated_transactions` have normalized display `amount`, category and `internal_transfer_flag`; TP-20261017-003 adds authoritative `reporting_flow_kind` and reasons.

## Ordered edits (do not rediscover)
1. `frontend/src/components/modals/TransactionModal.vue::summary`: aggregate **only backend `reporting_flow_kind === 'income'|'expense'`** for economic bars; account movement and unknowns are separate totals. Use backend-supplied signed economic amount when present; if missing classification, use `unclassified` not sign-based Income. Expense remains visually negative. Add unobtrusive row under existing three totals: `Transfers in/out`, `Debt payments`, `Needs classification` when present; distinguish **economic net** from cash movement. Keep existing modal, not a replacement.
2. `frontend/src/components/tables/ModalTransactionsDisplay.vue`: keep transfer rows visible (including `include_transfers=true` owner-scoped API), style as neutral/transfer rather than green wage income or red consumer purchase. Show accessible small category label `Transfer` / `Review`, with reason available in tooltip/title, no false "verified" badge; retain click-to-open Transactions editing. Preserve mobile overflow and keyboard behavior.
3. `frontend/src/views/Dashboard.vue::onNetBarClick`: request same date/account scope as chart, with `include_transfers=true`; reconcile aggregated economic subtotals/counts against clicked chart point via shared backend results. If API `total > page_size`, page through **bounded** results or display visible `partial activity, totals based on full period` warning using authoritative server summary, never assert first 1000 rows equal whole day. After classification edits or transfer confirmation, refresh chart and modal together through existing invalidation mechanism, not a new polling system.
4. `frontend/src/components/charts/DailyNetChart.vue` and `frontend/src/components/dashboard/NetOverviewSection.vue`: preserve existing chart architecture; labels/tooltip/summary must state `Economic Income` (or `Income, excluding transfers`), `Expense`, `Net`; do not aggregate investment deposits as earned income. If helpful, show neutral `Transfers` drilldown count without including them in income bars. No overall restyle.
5. `docs/frontend/DAILY_NET_CHART.md` / `docs/frontend/DASHBOARD_MODAL_GUIDE.md`: document cash movement vs economic activity and how to review uncertain transfers.

## Contract fixtures
- Oct 13 synthetic transactions: own Zelle +$200, suspected unpaired brokerage deposit +$100, student debt cash payment -$131.64, Adobe -$12.89 and -$21.49, credit interest -$265.71. `Income` on chart **and modal = $0** from these two credits; Zelle neutral confirmed transfer, bank transfer marked review; actual expense/debt splits follow 003 (do NOT assume all -$431.73 is consumption).
- Genuine payroll +$1000 remains economic income, merchant refund +$25 does not. Confirm pair -> requery and change both surfaces. All entries remain accessible.
- Date-only click, no rows, errors, 1,001 rows / pagination, 390px/1280px, screen-reader labels. Reconcile sums and split counts across modal/chart; no frontend guessed finance classifications.

## Files, validation, non-goals
Tests: `frontend/src/components/modals/__tests__/TransactionModal.spec.js`, `frontend/src/components/charts/__tests__/DailyNetChart.spec.js`, `frontend/src/views/__tests__/Dashboard.spec.ts`, `frontend/cypress/e2e/dashboard.cy.js`. Run `cd frontend && npm run test -- --run src/components/modals/__tests__/TransactionModal.spec.js src/components/charts/__tests__/DailyNetChart.spec.js src/views/__tests__/Dashboard.spec.ts && npm run build`; run backend `pytest tests/test_charts_daily_net.py -q`.
No new transfer detector, no bank-data mutation, no CSS redesign, no paid provider calls.
Implementation: read AGENTS + packet README/INDEX/TRACKER, start In Progress, reuse 003 classification, validate, commit only packet-owned changes directly to main without force, then mark Complete/move packet and update index/tracker atomically. Record exact date fixture sums, commands/results, and blocker if backend not runnable.

## Completion report (2026-10-18)

- Backend: `backend/app/sql/account_logic.py` rows now include `signed_account_delta` and `economic_amount` (None for non-economic kinds). `tests/test_charts_daily_net.py::test_row_economic_amounts_reconcile_with_the_daily_net_buckets` asserts row sums equal each chart day bucket (income, expenses, refunds, net, transfer and unclassified counts); 11 passed.
- Frontend: `utils/flowSummary.js` and `utils/dailyModal.js` (new), `TransactionModal.vue`, `ModalTransactionsDisplay.vue`, `Dashboard.vue::onNetBarClick`, with specs. Oct 13 fixture result in `flowSummary.spec.js`: income $0, expense -$300.09 (Adobe -12.89, -21.49, interest -265.71), net -$300.09, transfer in $200 (1), debt payment $131.64 (1), 1 row needing classification ($100); payroll +$1,000 is income and refund +$25 is a refund.
- Deviation: the packet's "server summary" for >page_size days does not exist; `onNetBarClick` pages up to 5 x 1,000 rows and otherwise shows a "Partial activity" notice. Classification-edit refresh relies on the dashboard refetching on return (no new invalidation channel). `DailyNetChart.vue`/`NetOverviewSection.vue` were not changed: tooltip labels already come from the 003 contract and the docs now state the economic meaning.
- Tests: vitest `flowSummary`, `dailyModal`, `TransactionModal`, `ModalTransactionsDisplay`, `DailyNetChart` pass; `Dashboard.spec.ts` still has the same 30 failures as `main` (verified with a stash); `npm run build` succeeds. No Cypress run or screenshots at 390px/1280px.

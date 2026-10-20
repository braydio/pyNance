# TP-20261019-005: Investment, Planning and Recurring Ledger Summaries

**Packet ID:** TP-20261019-005  
**Status:** Ready  
**Created:** 2026-10-19  
**Last updated:** 2026-10-19  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/active/TP-20261019-005-domain-ledger-breakdowns-and-qa.md`  
**Priority:** P2  
**Workstream size:** One independently testable implementation packet  
**Depends on:** TP-20261019-003 and TP-20261019-004  
**Series:** Four packets (002 → 003 → 004 → 005), ordered due to shared summary/style contracts.

## Outcome
Complete the “all tables” audit for **table-like lists and domain-specific grids not in `components/tables/`**. Give each ledger useful group subtotal, filtered-scope count, unfiltered comparator when supported, and table-like visual polish based on shared 003/004 tokens. No spurious sum of unlike financial measures.

## Confirmed seams on main 360fb21dc5a60d5d7cb93508a214584eba07f1de
- `frontend/src/views/Investments.vue`: `holdings-table`, `tx-table` are DIV-based grid rows, not semantic HTML table; holdings already exposes `filteredTotal`, `portfolioTotal`, `summarizedHoldings`, `totalsByInstitution`, but the filtered/whole-scope comparison is visually fragmented. `txData` shows a paginated investment transaction grid with no explicit amount-subtotal scope.
- `frontend/src/components/accounts/AccountPortfolioList.vue`: “Showing X of Y” and grouping by type→institution, but no consistent group subtotal headline as account balances differ in sign/type.
- `frontend/src/components/recurring/RecurringTransactionSection.vue`: Needs review / Confirmed & upcoming / Ignored & ended groups. Suggestions are **not confirmed bills**, so they must not be counted as committed reserves.
- `frontend/src/components/planning/BillList.vue`: due-first list with name/amount/frequency/expanded details, but no subtotal for a selected forecast scenario/period.
- `frontend/src/components/transactions/InternalTransferScanner.vue` and `TransactionReviewModal.vue`, `frontend/src/components/forecast/ForecastBreakdown.vue` and `ForecastSummaryPanel.vue` (inspect actual available filename in `frontend/src/components/forecast/` before edit): grouped lists/row grids need the same overflow and hierarchy review without converting financial classifications.

## Ordered implementation
1. `frontend/src/views/Investments.vue`: consolidated summary row above holdings showing “Filtered holdings value”, “Entire connected holdings value”, holding count and #accounts; existing `filteredTotal/portfolioTotal` remain the source, preserve selected account/institution. Group subtotal by institution/account once, not both duplicated as independent portfolio totals; each expandable account summary reconciles to child holdings. Investment transaction grid gets page count and **page activity subtotal** only, unless backend supports all-matching filtered amount; buys, sells, transfers and dividends must be separate labeled categories based on provider type, never one misleading “profit” amount. Turn grid into semantic `<table>` with expandable child rows when practical, else `role=table/row/columnheader/cell` with full accessible sorting.
2. `frontend/src/components/accounts/AccountPortfolioList.vue`: show group count + **asset value** and **liability balance** in separate columns/labels, not one “cash” sum; use shared `frontend/src/utils/accountPortfolio.js` or `account_portfolio_metrics` output. Missing/stale balances and hidden-account inclusion explicit. Sort/group choice never silently changes unfiltered comparator.
3. `frontend/src/components/recurring/RecurringTransactionSection.vue` and `frontend/src/components/planning/BillList.vue` / `PlanningSummary.vue`: relevant **upcoming-period** total (e.g., due in next 30 days) only for confirmed, date-bounded obligation instances. Separate income vs outflows, confirmed vs candidates vs ignored/ended, fixed vs estimated; no blind summation of monthly + annual recurrence amounts or multiplying across time without supported dates; if due instances unavailable, label an aggregate “listed plan amounts, mixed cadence” **without** calling it a monthly total. Scenario planning can sum only that scenario's visible bills; never leak global scheduled expenses into an alternate plan without explanation.
4. `frontend/src/components/transactions/InternalTransferScanner.vue`, `TransactionReviewModal.vue`, `frontend/src/components/forecast/ForecastSummaryPanel.vue`, and actual existing forecast breakdown components: compact review counts/coverage, type-aware grouped subtotals **when the source already supplies them**. Transfers/review rows neutral, debt principal vs expenses and cash projection vs historical net clear. No extra API if no matching all-filtered summary exists; display “Loaded items only” when partial, never falsely claim dataset total.
5. Apply table anatomy from 003 and surface roles from 004 to these grids/lists; increase usable density without text collision, keep expandable actions keyboard-operable and contents accessible. Prefer group header with unobtrusive subtotal to scattered cards; no nested identical outlines. Convert DIV grid to semantic table where feasible. Do not change financial math upstream or create another classifier.
6. Record audited inventory and disposition in `docs/frontend/LEDGER_TABLE_AUDIT_2026-10-19.md`: Inventory of canonical tables `AccountsTable,InstitutionTable,MasterTxidTable,ModalTransactionsDisplay,TransactionsTable,UpdateTransactionsTable` and non-tables `Investments,AccountPortfolioList,RecurringTransactionSection,BillList,InternalTransferScanner,TransactionReviewModal,ForecastSummaryPanel`; for each name state data source, row scope, totals scope, missing/stale behavior, filter ownership, visual status, tests. Mark legacy/unused components as “legacy checked, no new KPI without data” rather than quietly omitting them.

## Acceptance
- Change account/inst/holdings/transaction/recurring filters and all displayed subtotals update to matching **full local collection** or explicitly labelled fetched page; totals don't change merely from pagination/sort; as-of label and missing data shown.
- Asset/liability, investment holdings value, investment transactions movement, recurring cash obligations and forecast scenarios never collapse into a meaningless generic “Net”.
- Empty/partial/error; single-vs-multiple selected accounts; mixed frequency, estimated/confirmed candidates, refunded/pending/movement transactions all handled. 390/768/1280px screenshots, keyboard expansion and focus, no horizontal body overflow.
- `cd frontend && npm run test -- --run src/views/__tests__/Investments.spec.js src/components/accounts/__tests__/AccountPortfolio.spec.js src/components/recurring/__tests__/RecurringTransactionSection.spec.js src/components/planning/__tests__/BillList.spec.ts src/components/planning/__tests__/PlanningSummary.spec.ts src/components/transactions/__tests__/InternalTransferScanner.spec.js src/components/transactions/__tests__/TransactionReviewModal.spec.js && npm run build`; backend route/summary tests if changed.
- No provider fetch to calculate display-only totals, no schema changes, no mistaken all-matching claim, no redundant panels. **Owner:** investments/domain ledger components above, docs audit; avoid touching dashboard composition and canonical table components unless justified blocker logged in tracker.


## Execution and closeout
Follow `AGENTS.md` and `docs/task-packets/README.md`: pause `scripts/dev-watcher.sh` only if running, preserve unrelated dirty files; inspect only named seams, mark packet/TRACKER In Progress, implement focused scope and tests, then mark Complete/move to completed and update INDEX/TRACKER in the same committed change. Sync/push `origin/main` without force, resume watcher if paused. Provide exact `Workstream`, status, commit link, changed files, totals/visual acceptance evidence, executed commands/results, unrun checks and blockers. Do not mark a failing or unverified test as passed.

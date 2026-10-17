# TP-20261016-009: Transactions Insights, Review Queue, Sorting and Filtering

**Packet ID:** TP-20261016-009  
**Status:** Ready  
**Created:** 2026-10-16  
**Last updated:** 2026-10-17  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/active/TP-20261016-009-transactions-insights-review-workbench.md`  
**Workstream size:** One targeted implementation packet  
**Priority:** P1  
**Depends on:** TP-20261016-001, TP-20261016-003, TP-20261016-005  
**Series:** 11 packets (TP-20261016-001..011); assume each named prerequisite has landed before starting this packet.  

## Objective
Transactions Insights, Review Queue, Sorting and Filtering. Complete only the named workstream; no broad rediscovery.

## Do not rediscover: exact file/ownership map
- `backend/app/routes/transactions.py`
- `backend/app/services/transaction_insights.py (new)`
- `frontend/src/views/Transactions.vue`
- `frontend/src/components/transactions/TransactionsActionsSidebar.vue`
- `frontend/src/components/tables/UpdateTransactionsTable.vue`
- `frontend/src/composables/useTransactions.js`
- `frontend/src/services/api.js`
- `frontend/src/components/transactions/TransactionInsightsPanel.vue (new)`
- `tests/test_transaction_insights.py (new)`
- `frontend/src/views/__tests__/Transactions.spec.js`
- `frontend/src/components/tables/__tests__/UpdateTransactionsTable.spec.js`

## Confirmed current seam (main at authoring 437bdd9cda1bd21d651e7c0ecd24c205d76b6ebc)
Transactions screenshot has big table dominated by nested X/Y scroll and separate pagination; top-level dates/accounts/types plus category/subcategory/column filters fragmented. `Transactions.vue` defines `filterSummary` from `filteredTransactions` in the current loaded page, yet displays generic `x shown` / `Total $...` as if entire matching set. `Scanner` gets renamed to `Transfer Review` by 003; `Recurring` gets canonical review by 005.

## Required code edits, in order
1. Add `transaction_insights.py:get_insights(owner_id,start_date,end_date,account_ids,categories?)` with SQL aggregates over ALL qualifying posted rows, not paginated client rows: `{matching_count,loaded_count?,gross_spend,refunds,net_spend,inflow,fees,uncategorized_count,review_items:[{id,kind,priority,transaction_ids,explanation}],recurring_candidate_count,transfer_pair_count,coverage}`. Exclude transfers from spend/income by is_internal/verified pairs; distinguish card payments/uncertain classification; use canonical amount semantics 001 and consistent currency. Detect only defensible heuristics `bank_fee`, `possible_duplicate_same_merchant_amount_day` (never claim duplicate), `missing_category`, `transfer_candidate`; max 20 items and evidence labels, no LLM. Owner-bound same principal security as other routes.
2. `backend/app/routes/transactions.py` new `GET /api/transactions/insights?start_date=YYYY-MM-DD&end_date=...&account_ids=...` validate scope, 366d max, no raw user_id as auth, compute counts via SQL `COUNT` not loading all, explain unavailable if no trusted principal; error 400/403 and 503 gracefully; no endpoint introduced for external vendor.
3. `frontend/src/views/Transactions.vue`: introduce compact summary metrics (Spending, Needs Review, Recurring Candidates) and prioritized actionable queue above explorer. One toolbar with search, period preset, account, sort (`Newest`, `Oldest`, `Largest spend`, `Amount`, `Merchant`, `Category`), Filter button; Advanced disclosure holds date, type, category, merchant, tags and column visibility. Preserve CSV export all filtered rows and saved filters, show `10 on this page · 2,005 matching` not `30 shown` unless truly loaded; label signed total precisely if shown. Review-card clicks apply a filter or focus target; no auto-mutating finance records.
4. `UpdateTransactionsTable.vue`: preserve edit and explicit columns functionality; remove fixed min 50vh inner vertical scroll for paginated 10/25-row view, keep local horizontal overflow for wide columns; sticky table head only when useful; amounts right-aligned; keyboard sort with aria-sort, 2-line merchant/category where safe. Distinguish related transfer/refund rows; no new duplicate table component. Rename top tabs `Activity`, `Recurring`, `Transfer Review` as 003; default activity remains.
5. Use unified recurring/transfer counts from packets 003/005, not per-page rescans on every mount; server cache TTL 5-15m keyed by owner+filters or only refresh on explicit user action; invalidate on edit/refresh. Avoid extra Plaid calls.

## 2026-10-17 downstream integration: consistent income semantics
**Do not implement a parallel metric.** This packet's `transaction_insights.py` must consume `transaction_flow_classification.classify_reporting_flow` from TP-20261017-003 and share owner/date scope with `charts.get_daily_net`; its `inflow` field must be expressly labeled economic income vs all credit cash movements (add separate transfers/unclassified subtotals). Pass confirmed transfer changes to the Daily Net and modal refresh in TP-20261017-004. For the Oct 13 synthetic fixture, Zelle +200 and ambiguous brokerage credit +100 are not +300 income. TP-20261017-004 owns chart/modal UI; do not redesign them here.

## Exact contracts and acceptance fixtures
- Insight counts reflect all matching records, not page slice. Card purchase is not income because signed incorrectly; fees are category/counterparty evidence; possible duplicates are labeled possible, never automatically removed.
- Click Review queue item filters/opens transaction; calendar/user account selection correctly scopes counts; CSV export retains whole filtered scope.

## Validation commands
`pytest tests/test_transaction_insights.py tests/test_transfer_analytics_exclusion.py -q`; `cd frontend && npm run test -- --run src/views/__tests__/Transactions.spec.js src/components/tables/__tests__/UpdateTransactionsTable.spec.js && npm run lint && npm run build`; Cypress 390/1280, page 1 of 200, matched_count vs loaded.

## Non-goals
No new financial transaction auto-edits; no paid API, no full analytics chart dashboard, no removal of advanced data explorer.

## Implementation/handoff
Read `AGENTS.md`, `docs/task-packets/README.md`, `INDEX.md`, `TRACKER.md`; validate only named symbols against latest main. Set In Progress in tracker before coding. Treat prerequisite packets as implemented, do not re-implement their features. Run focused tests then lint/build; commit only this workstream to main without force, mark Complete, move this packet to completed and update INDEX/TRACKER atomically. Report changed files, test output, fixture/behavior evidence, and deviations. If principal is not trusted, fail closed on new owner-scoped endpoints, not permissive fallback. Do not use Plaid Enrich/new billable APIs.

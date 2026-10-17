# TP-20261016-009: Transactions Insights, Review Queue, Sorting and Filtering

**Packet ID:** TP-20261016-009  
**Status:** Complete  
**Created:** 2026-10-16  
**Last updated:** 2026-10-17
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/completed/TP-20261016-009-transactions-insights-review-workbench.md`  
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

## Completion report (2026-10-17)

- **Order note:** this packet consumes `classify_reporting_flow` from TP-20261017-003, so that packet was implemented first (its dependency note in this packet says so). TP-20261017-004 (chart/modal UI) is untouched.
- **Backend.** `backend/app/services/transaction_insights.py` (new): `get_insights(owner_id, start, end, account_ids, categories, refresh)` over ALL posted, visible rows in scope (range <= 366 days): `matching_count` via SQL `COUNT`, `gross_spend`, `refunds`, `net_spend`, economic `income`, an explicitly labelled `inflow {economic_income, all_credit_movements, refunds, transfers_in, debt_settlement_in, investment_in, unclassified_in}`, `fees`, `uncategorized_count`, `recurring_candidate_count` (proposed detected streams from TP-004/005), `transfer_pair_count` (TP-003 candidate finder) and `coverage`. At most 20 rule-based `review_items` (`transfer_candidate`, `possible_duplicate_same_merchant_amount_day` worded "Possible duplicate", `bank_fee`, `missing_category`), each with evidence labels, <= 10 transaction ids and a UI filter; no LLM or external service. Ten-minute in-process cache keyed by owner and filters, bypassed by `refresh=true` and dropped by `invalidate_tx_cache()` (edits and refreshes). `GET /api/transactions/insights` is bound to the trusted server owner (503 without one, 400 for bad scope).
- **Server-side sort.** `get_transactions` accepts `sort` (`date_desc` default, `date_asc`, `spend_desc`, `amount_desc`, `merchant_asc`, `category_asc`) applied across every matching row, not just the loaded page (unknown value -> 400); the cache key includes it.
- **Frontend.** New `TransactionInsightsPanel.vue`: Spending (net, with spent/refunded), Income (earned only, with "Other credits ... transfers ... unreviewed" so credits are never called income), Needs review, Recurring candidates, the matching count, and the prioritized review queue; cards only emit an action. `Transactions.vue`: panel above the explorer with an explicit scope label; one toolbar with search, Period preset (All time / Last 30 days / This month / Last 90 days / Year to date, reading "Custom" for manual dates), Account, Sort and "Advanced filters"; honest counts ("10 on this page · 2,020 matching", "N found in loaded pages" while searching, "This page, signed total ..." instead of an unqualified Total); the toolbar sort goes to the server and switches the loaded-page client sort off; review cards open Transfer Review or set the search/date filter and never edit a record; CSV export still pages through the whole filtered set (unchanged). `UpdateTransactionsTable.vue`: paginated pages now scroll with the document (horizontal overflow only, sticky head and inner height cap only for the virtualised view); transfer / refund / debt-payment / investment / needs-review badges from `reporting_flow_kind`; existing aria-sort headers, right-aligned amounts and editing preserved. `api.getTransactionInsights` added.
- **Tests.** `tests/test_transaction_insights.py` (9: totals over every row, Oct 13 credits are not $300 income, review items and the "possible" wording, 20-item and 10-id caps, scope/other owners/accounts/categories, validation and fail-closed, unified recurring and transfer counts with no mutation, caching/refresh/invalidation, server-side sort across all rows); `TransactionInsightsPanel.spec.js` (5), `Transactions.spec.js` (16, +7: insights scope and params, honest counts, server sort, preset, review cards, owner-missing message), `UpdateTransactionsTable.spec.js` (+3: badges, scroll behavior, aria-sort). `npm run build` passes; ESLint 0 errors; backend per-file suite has the same pre-existing failures as before and nothing new.
- **Real-browser check (headless Chrome, real data via an isolated backend, not your :5000 server):** 1280px and 390px, Nightfox, no horizontal overflow; summary and review queue render; the toolbar is a single row at 1280 after fixing select widths; the table grows with the page with no inner scroll box; real rows show "Debt payment" / "Investment" badges. Everforest and Cypress (390/1280 e2e, page 1 of 200) were not run; the Cypress binary is not installed here.
- **Deviations / notes:** (1) the "Needs review" metric counts transactions across the review items, so it includes informational fee items; (2) "Advanced filters" holds dates, type and the existing explorer controls (category/merchant/tags/columns stay in the table's own filter bar); a dedicated category/merchant control was not added; (3) the summary defaults to the last 30 days when no period is chosen and says so; (4) `tx_type=credit|debit` in the explorer still filters on the raw stored sign (pre-existing).

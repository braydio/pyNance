# TP-20261019-002: Filter-Aware Financial Table Totals and Scope Contract

**Packet ID:** TP-20261019-002  
**Status:** Complete  
**Created:** 2026-10-19  
**Last updated:** 2026-10-19  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/completed/TP-20261019-002-filter-aware-table-summary-contract.md`  
**Priority:** P0  
**Workstream size:** One independently testable implementation packet  
**Depends on:** None; use completed economic-flow TP-20261017-003/004  
**Series:** Four packets (002 → 003 → 004 → 005), ordered due to shared summary/style contracts.

## Outcome
Every financial table distinguishes **all rows matching active filters** from **currently displayed/page rows**, and separates economic activity from balance movement. A page subtotal must not impersonate the filtered dataset total. This is the shared data prerequisite for 003, 004 and 005.

## Confirmed seams on main 360fb21dc5a60d5d7cb93508a214584eba07f1de
- `frontend/src/views/Transactions.vue::filterSummary` sums `pageRows`, is shown only with top-level filters, and says “This page, signed total”. No all-matching financial aggregate appears alongside it.
- `frontend/src/composables/useTransactions.js` fetches/cache-prefetches pages and uses client `Fuse` search on **cached/loaded pages**. Search counts therefore are not necessarily the complete backend match set.
- `frontend/src/components/tables/UpdateTransactionsTable.vue::filteredTransactions` adds independent field/category/subcategory filters **after** parent pagination; `paginatedFilteredTransactions` then slices using `currentPage` again. Parent summary cannot observe these filters and may double-page. Sorting may also happen on loaded rows rather than all matches.
- `backend/app/routes/transactions.py::get_transactions_paginated` calls `backend/app/sql/account_logic.py::get_paginated_transactions`, which has the authoritative date/account/category/merchant/tags/sort/tx_type query predicates and count; `GET /api/transactions/insights` handles only a subset of these filters and is a review summary, **not** a complete table-totals API.
- The economic classifier `backend/app/services/transaction_flow_classification.py` already distinguishes `income|expense|refund|transfer|debt_settlement|investment_movement|unclassified`. Raw amount sign and transfers must not be relabeled as earned income / spending.

## Ordered changes; do not rediscover
1. **Canonical filter contract.** Add reusable validated filter parsing/query building near `backend/app/routes/transactions.py::get_transactions_paginated` and `backend/app/sql/account_logic.py::get_paginated_transactions` (new helper e.g. `build_transaction_filter_query`). Preserve existing endpoint compatibility. Accept `start_date,end_date,account_ids,tx_type,category,merchant,tags,search` plus the actual field filters surfaced by `UpdateTransactionsTable`, with explicit searchable fields and consistent case-insensitive text matching. Make search **server-side across all matching rows**, rather than describing a subset of cached pages as the complete search. Keep the route's sort and pagination. Use parameterized SQL; validate account ownership/filter dimensions; trusted `PYNANCE_OWNER_USER_ID` for **new financial summary** is mandatory and fails closed 503 if unavailable. Never expose cross-owner, hidden or pending transactions in the new aggregate. Honor the table's current explicit transfer-inclusion semantics, not a silent changed default.
2. **Aggregate endpoint.** Add `GET /api/transactions/summary` (or an explicitly named sibling under the existing transactions blueprint), consuming **the identical filtered relation** as table results, without applying page/limit/order and without fetching all matching rows into JS. Return decimal-cent financial totals, counts and coverage:
   ```json
   {
     "status":"success",
     "data":{
       "scope":"all_matching","matching_count":0,
       "income":0,"expenses":0,"refunds":0,"economic_net":0,
       "transfers_in":0,"transfers_out":0,"debt_settlements":0,
       "investment_movements":0,"unclassified_in":0,"unclassified_out":0,
       "needs_review_count":0,
       "breakdowns":{"by_category":[],"by_account":[],"by_month":[]},
       "as_of":null,"applied_filters":{}
     }
   }
   ```
   Use existing reporting classifier and `economic_amount` exactly once. `expenses` negative, `refunds` separate positive, `economic_net = income + expenses + refunds`. Group breakdowns are **additive only within compatible categories** and reconcile to the same population. No misleading combined portfolio cash-balance “net” from multi-account transfers. Null/unavailable classifications are counted separately, never defaulted to income. Avoid N+1 classification lookups and unbounded pagination; batch accounting read-only. Distinguish data as-of and partial provider coverage. For prior budgeted `insights`, leave its review queue intact.
3. **One filter owner.** Update `frontend/src/views/Transactions.vue`, `frontend/src/composables/useTransactions.js`, `frontend/src/components/tables/UpdateTransactionsTable.vue` and `frontend/src/api/transactions.js`: lift nested field/category filters into a shared parent query state (or emit a canonical filter-change event and derive one request key); backend filtered table, matching count, export and aggregate all receive identical filters. Never quietly apply a second local-only filter while labeling the global summary “all matching”. If a legacy component cannot be migrated in this packet, mark **Loaded page only** explicitly and disable global-total claim for that filter, but the primary Transactions Activity table must have full parity by acceptance.
4. **Two separate presentation models.** Add shared frontend `tableSummary` adapter/composable near `frontend/src/utils/flowSummary.js` or `frontend/src/composables/`, with response-race guards keyed by canonical filter hash; `matchingSummary` is server-side all-match; `visiblePageSubtotal` computed from **actually rendered non-placeholder rows**. Do not add fake totals for virtual spacer rows, make placeholders count, or infer missing `0` from network failure. Reset/update on edit, hide, transfer confirmation, sort/filter/page/refresh as applicable (sorting/page does not change all-match aggregate). Avoid fetching paid providers or running bulk client pagination.
5. **Scope language.** “Filtered results · N matches” vs “Page 2 of 12 · 15 shown”; “Economic income (excl. transfers)”, “Economic expenses”, “Refund adjustments”, “Economic net”; separate “Transfers / debt payments / Needs review” foldout. Plain signed activity total is allowed only as **cash movement (current page)** with explicit sign basis, not mislabeled net income. If data is stale/error, preserve last values only if visibly stale; never imply a successful refresh.

## Synthetic acceptance
- 51 matching rows, 15/page; page 2 subtotal uses its 15 displayed rows; filter summary covers all 51 independent of page and sort. Search and **nested category/field filter** narrow *both* count and summary (not merely a cached-page subset); export respects same filter.
- Economic fixture: payroll +1000, expense -300, refund +25, own transfer +200/-200, credit-card settlement 131.64, unclassified +100: economic income 1000, expenses -300, refunds 25, net 725; movement/review excluded. Cross-owner/hidden/pending omitted; 503 if owner missing. Cent-accurate sums and subgroup conservation.
- 0-match, error, provider incomplete, rapid filter changes, multiple accounts, 1,001+ rows, edits and pagination each show accurate scope and no request race.
- `pytest tests/test_api_transactions.py -q`, `pytest tests/test_account_logic_transactions.py -q`, `pytest tests/test_transaction_flow_classification.py -q`, new `tests/test_transaction_summary.py -q`; `cd frontend && npm run test -- --run src/views/__tests__/Transactions.spec.js src/composables/__tests__/useTransactions.spec.js src/components/tables/__tests__/UpdateTransactionsTable.spec.js && npm run build`.
- Documentation: `docs/frontend/TRANSACTIONS_TABLE_SUMMARIES.md` (new): exact filters, counts, sort, subtotals, economic vs cash movement contract.
- Non-goals: no schema migration, no banking data mutation, no second classifier, no broad redesign, no paid service calls. **Owner:** API/query/transaction filter/summary state only. Workstream 003 owns visuals.


## Execution and closeout
Follow `AGENTS.md` and `docs/task-packets/README.md`: pause `scripts/dev-watcher.sh` only if running, preserve unrelated dirty files; inspect only named seams, mark packet/TRACKER In Progress, implement focused scope and tests, then mark Complete/move to completed and update INDEX/TRACKER in the same committed change. Sync/push `origin/main` without force, resume watcher if paused. Provide exact `Workstream`, status, commit link, changed files, totals/visual acceptance evidence, executed commands/results, unrun checks and blockers. Do not mark a failing or unverified test as passed.

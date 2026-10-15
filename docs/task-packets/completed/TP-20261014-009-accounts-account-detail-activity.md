# TP-20261014-009: Account drill-in, truthful activity and range integrity

**Packet ID:** TP-20261014-009  
**Status:** Complete  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/completed/TP-20261014-009-accounts-account-detail-activity.md`  
**Workstream size:** One independently testable implementation packet  
**Depends on:** TP-20261014-008  
**Priority:** High  
**Series:** Accounts audit 5 of 5  
**Audited paths:** Accounts frontend and backend on 2026-10-14; prior head d38bd3d  

## Objective
Account drill-in, truthful activity and range integrity. Implement against current main with no repository-wide rediscovery.

## Current state and exact implementation

**Current seams**
- `frontend/src/views/Accounts.vue:loadActivityBreakdown`: `fetchRecentTransactions(account.account_id,100)` for every account, ignores selectedRange, truncates high-volume histories, calls them "in selected date range"; `Promise.allSettled` swallows partial failures as empty.
- `frontend/src/api/accounts.js:rangeToDates`: 30d uses `start=end-days`, 31 inclusive days, and `toISOString()` UTC shift. Selected account `fetchRecentTransactions(id,10)` also disregards range.
- `backend/app/routes/accounts.py:account_net_changes` currently calls signed transaction positive "income", negative "expense" and legacy balance history "net_change": credit card payments/transfers are not ordinary salary or spending.
- `frontend/src/components/charts/AccountBalanceHistoryChart.vue` fixed 400px height; chart not enough to contextualize an account.

**Implement**
1. `frontend/src/views/Accounts.vue` focused account summary: name/type/institution/mask, last sync and connection, current balance / amount owed; credit limit, utilization + unknown coverage, reported available credit or explicitly derived remaining, APR breakdown with provider/manual/estimated source, observed interest last 30 days; provider-supplied due/min payment only when available. Deposits show current vs available cash, loans interest rate/balance and no card utilization, investments show value and link to existing /investments (verify in `frontend/src/router/index.js`). No repeated large KPI array.
2. Render selected-account balance history 7/30/90/365, then last transactions and link to existing /transactions (only append account filter if destination supports it), then secondary trends. "Back to all accounts" returns Overview without dropping shared portfolio controls.
3. Backend `backend/app/routes/accounts.py`: add GET `/api/accounts/activity_breakdown` accepting strict YYYY-MM-DD inclusive start/end, safe account owner scoping, aggregate via SQL per account without 100 cap. Return count, sum ABS(amount) as `transaction_value_abs`, period, coverage, explicitly chosen pending/internal transfer treatment; no account ID enumeration across users. Prefer single query over N account requests.
4. `frontend/src/api/accounts.js`: new `fetchAccountActivityBreakdown(params)`; replace `loadActivityBreakdown` N calls; correct `rangeToDates` start=end-(days-1) in LOCAL calendar dates; use `frontend/src/api/transactions.js:fetchTransactions({account_ids:[accountId],start_date,end_date,page:1,page_size:10})` for selected account's range-specific list. One period governs movement, chart, activity list and ranked counts. Display independently failed sections and refresh tokens to avoid stale selection races.
5. `frontend/src/views/Accounts.vue`: relabel Net Change Summary "Money movement in selected period" (money in/out/net movement), avoid calling payment income/savings; net balance delta distinct from transaction volume; explain pending/transfers briefly. Remove redundant mounted+watch double fetch, handle `loadAccounts` errors with retry; keep refresh and reconnect unaffected. Only show controls useful per account type; sort latest tx by date/amount via existing TransactionsTable if supported, not rewritten wholesale.

**Tests** New `tests/test_accounts_activity_breakdown.py` for >100, bounded dates, pending/internal, owner isolation, invalid dates, hidden state, empty; update `frontend/src/views/__tests__/Accounts.spec.js`, `AccountsRetry.cy.js`, new `frontend/src/api/__tests__/accounts.spec.js`. Commands `pytest -q tests/test_accounts_activity_breakdown.py`; `cd frontend && npm run test -- --run src/views/__tests__/Accounts.spec.js src/api/__tests__/accounts.spec.js && npm run lint && npm run build`.

**Non-goals** No new investment portfolio system, credit score optimization, loan payoff forecasting, or review workflow rewrite. **Accept:** period-aligned >100 counts, truthful balance/movement/APR source, clear user action and partial failure behavior.


## Implementation order and closeout
1. Check `AGENTS.md`, `docs/task-packets/README.md`, `INDEX.md`, `TRACKER.md`; validate named seams only.
2. Mark In Progress in packet and tracker. Complete changes in order listed; run focused tests then lint/build/available guards. For migrations verify dev DB target and live revision head first.
3. On pass mark Complete, move packet to completed/, update INDEX/TRACKER in same change, commit only packet-owned changes to origin/main with normal synchronization; never force push.
4. Report files changed, contracts, tests (honestly), screenshots if UI, deviations and exact blocker/resume condition.

## Do not rediscover
Avoid broad repo archaeology. Only inspect explicitly named paths, directly imported helpers/tests, and exact migrations/route registrations needed to implement this packet.

## Completion report

- Backend: new `GET /api/accounts/activity_breakdown` (strict inclusive `YYYY-MM-DD`, single grouped SQL query with no 100-row cap, `count` + `SUM(ABS(amount))` as `transaction_value_abs`, optional `account_ids`/`user_id`/`include_hidden`/`include_pending`, pending excluded by default, internal transfers included and reported separately, coverage + treatment in the response, unknown/other-owner IDs indistinguishable from nonexistent). `net_changes` now excludes pending and adds `money_in`/`money_out`/`net_movement`/`transaction_count`/`balance_change` while keeping `income`/`expense`/`net` aliases. API reference and routes docs updated.
- Frontend: `api/accounts.js` `rangeToDates` now returns exactly N inclusive local calendar days (no UTC shift) and `fetchAccountActivityBreakdown` replaces the N-request fan-out. `Accounts.vue`: one Period control governs money movement, balance chart, latest-transactions list (`fetchTransactions({account_ids, start_date, end_date, page_size: 10})` with "Showing X of Y"), and the ranked activity list; per-section loading/error with request tokens so stale responses are dropped; Net Change Summary relabelled "Money movement in selected period" with balance change shown separately; type-specific account facts (deposits current vs available, cards owed/limit/utilization/available vs calculated remaining/APR with source/observed interest/payment data only when provided, loans interest rate without utilization, investments link to /investments); link to `/transactions?account_id=` (supported by the Transactions page); accounts-load retry; single fetch cycle on mount.
- Tests: new `tests/test_accounts_activity_breakdown.py` (17), `frontend/src/api/__tests__/accounts.spec.js`, extended `Accounts.spec.js`; full vitest 56 files / 353 tests pass, lint 0 errors, build OK; backend accounts tests pass.
- Not run: Cypress (`AccountsRetry.cy.js` not modified; its selectors predate the current layout), live-DB/browser verification. `user_id` scoping is an opt-in query filter because the API has no authenticated user context yet.

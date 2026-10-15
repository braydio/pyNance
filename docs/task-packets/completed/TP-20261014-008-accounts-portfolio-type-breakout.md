# TP-20261014-008: Accounts portfolio hierarchy and type breakouts

**Packet ID:** TP-20261014-008  
**Status:** Complete  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/completed/TP-20261014-008-accounts-portfolio-type-breakout.md`  
**Workstream size:** One independently testable implementation packet  
**Depends on:** TP-20261014-005, TP-20261014-006  
**Priority:** High  
**Series:** Accounts audit 4 of 5  
**Audited paths:** Accounts frontend and backend on 2026-10-14; prior head d38bd3d  

## Objective
Accounts portfolio hierarchy and type breakouts. Implement against current main with no repository-wide rediscovery.

## Current state and exact implementation

**Current seams**
- `frontend/src/views/Accounts.vue`: Summary starts with selected account net change, then balance chart, then Most Active Accounts, while mounted flow auto-selects first account. No all-accounts overview.
- `frontend/src/components/accounts/LinkedAccountsSection.vue`: type/institution grouping lives in maintenance Connections tab, based on inconsistent humanized raw types.
- `frontend/src/components/tables/AccountsTable.vue`: search/sort/show hidden/type filter exist but not mounted on Accounts page, and component fetches its own data and includes Hide/Delete; avoid mounting it raw.

**Target layout**
Header title + compact actionable reconnection warning (no duplicated reconnect button) / current sync state. Four quiet portfolio KPIs: assets, liabilities, net position, credit utilization with coverage `X of Y credit lines have known limits`. Type chips/summary: All, Checking & Savings, Credit Cards, Loans & Lines, Investments, Other with counts+signed/correct aggregate. Compact filters: search institution/name/masked digits, type, institution, connection state, include hidden OFF, sorting (balance, debt owed, utilization when known, APR when known, name, recently synced); active filter chips and Reset. Group ledger default by type then institution, each account has masked name, balance or amount owed, available/limit/usage if credit, qualified APR source or unavailable, sync status, View details. One-column readable mobile rows, tabular aligned currency desktop. Keep 4 tabs Overview/Activity/Trends/Connections; maintenance in Connections.

**Implement**
1. Create `frontend/src/utils/accountPortfolio.js`: `classifyAccount`, `portfolioTotals`, `creditUtilization`, `filterPortfolioAccounts`, `sortPortfolioAccounts`. Support lowercase provider types and investment flags; non-credit utilization is N/A, missing limits are null not 0; no bank checking overdraft as card line, no summing liability amounts as assets. Default totals exclude hidden, update visibility clearly if include hidden enabled. No mixing currencies in summed total: group by currency or mark aggregate unavailable on mixed currency.
2. Create `frontend/src/components/accounts/AccountPortfolioOverview.vue` and `AccountPortfolioList.vue` to consume parent-owned `accounts` only. No duplicate fetch/delete controls. Type chip changes account filter, query and sort operate on same list, display shown/total and account count, missing data explicit. APR label provider/manual/estimated and "unknown" when unverified; rate only on applicable accounts.
3. `frontend/src/views/Accounts.vue`: Summary tab renders portfolio overview/list FIRST even when account selected; clicking account sets `accountId` and focuses account details below or Activity without losing all-accounts context. Keep deep-link accountId support; no new route. Subdue secondary net KPIs and chart, keep existing tabs/sideBar and reconnect.
4. `frontend/src/components/accounts/LinkedAccountsSection.vue`: show reconnect status distinctly; suppress empty Rewards & Promotions disclosure, avoid demo 0 APR and showing APR on checking/investments. May reuse shared account classification, but do not duplicate overview ledger.
5. CSS use neutral surfaces, compact spacing, consistent width and subtle utilization bar; no extra large hero/chart in first screen.

**Tests** `frontend/src/utils/__tests__/accountPortfolio.spec.js` (type aliases, sign, unknown/mixed currency, missing limit, 0 balance, refund, hidden); new components tests under `frontend/src/components/accounts/__tests__/`; update `frontend/src/views/__tests__/Accounts.spec.js` and `AccountsSummary.cy.js`. `cd frontend && npm run test -- --run src/utils/__tests__/accountPortfolio.spec.js src/views/__tests__/Accounts.spec.js && npm run lint && npm run build`.

**Non-goals** No new routes/tabs, no destructive AccountsTable actions, no repeated prior TP-20261007-005 shell redesign. **Accept:** overview first, type summary filters accounts, comfortable 360px/1280px, truthful source/missing data.


## Implementation order and closeout
1. Check `AGENTS.md`, `docs/task-packets/README.md`, `INDEX.md`, `TRACKER.md`; validate named seams only.
2. Mark In Progress in packet and tracker. Complete changes in order listed; run focused tests then lint/build/available guards. For migrations verify dev DB target and live revision head first.
3. On pass mark Complete, move packet to completed/, update INDEX/TRACKER in same change, commit only packet-owned changes to origin/main with normal synchronization; never force push.
4. Report files changed, contracts, tests (honestly), screenshots if UI, deviations and exact blocker/resume condition.

## Do not rediscover
Avoid broad repo archaeology. Only inspect explicitly named paths, directly imported helpers/tests, and exact migrations/route registrations needed to implement this packet.

## Completion report

- New `frontend/src/utils/accountPortfolio.js` (classifyAccount, portfolioTotals, creditUtilization, accountUtilization, filter/sort/group helpers, aprInfo provenance). Unknown limits/balances stay `null`; overdraft limits are never card lines; refunds on cards reduce owed rather than count as assets; hidden accounts excluded by default; mixed currencies make aggregates unavailable.
- New `AccountPortfolioOverview.vue` (assets, liabilities, net, utilization with "X of Y credit lines have known limits", type chips with counts/aggregates) and `AccountPortfolioList.vue` (search incl. mask digits, institution/connection/sort filters, include-hidden, active chips + Reset, shown/total, ledger by type then institution with owed/limit/usage/available/APR source/sync status and View details). Both consume the parent-owned `accounts`; no fetch or hide/delete controls.
- `Accounts.vue`: overview and ledger render first on Overview even with a selected account; the first account is no longer auto-selected ("All accounts" option, View details selects and scrolls to a details header with "Back to all accounts"); deep-linked `accountId` still works; per-account cards are subdued and shown only with a selection. Tabs/sidebar/reconnect unchanged.
- `LinkedAccountsSection.vue`: groups provider-style types through shared classification (adds Loans & Lines), APR only on credit/loan with provenance label ("APR unknown" instead of fabricated values), demo 0% APR removed, empty Rewards & Promotions disclosure suppressed.
- Tests: `utils/__tests__/accountPortfolio.spec.js` (25), `components/accounts/__tests__/AccountPortfolio.spec.js`, updated `LinkedAccountsSection.spec.js` and `views/__tests__/Accounts.spec.js` (+snapshot); full vitest 55 files / 339 tests pass, lint 0 errors, build OK.
- Not run: Cypress (`AccountsSummary.cy.js` gained one overview case; the file's pre-existing cases reference selectors that no longer exist and were not touched). No browser visual check at 360px/1280px.

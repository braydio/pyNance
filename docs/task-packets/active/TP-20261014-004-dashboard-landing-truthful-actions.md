# TP-20261014-004: Dashboard Landing Truthful Action Priority and Calm Copy

**Packet ID:** TP-20261014-004  
**Status:** Ready  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** docs/task-packets/active/TP-20261014-004-dashboard-landing-truthful-actions.md  
**Workstream size:** One landing-page information/behavior packet  
**Depends on:** TP-20261014-003 (same Dashboard/NetOverview components)  
**Priority:** High  
**Source reviewed:** main @ 4ef24fd358e4d630108420e4bacc98ec5733d278  
**Series:** 4 of 4

## Objective
Keep the existing TP-20261007-003 decision-first dashboard layout. Remove false urgency, duplicate calls, and sarcastic status copy; distinguish real required action (broken connections) from optional transaction browsing and from cashflow information.

## Confirmed current seams
- frontend/src/views/Dashboard.vue: loadReviewCount() does fetchTransactionsApi({page:1,page_size:1,...reviewFilters}) and uses result.total. frontend/src/api/transactions.js and backend/app/routes/transactions.py:get_transactions_paginated do NOT filter unreviewed status. frontend/src/components/transactions/TransactionReviewModal.vue:handleApprove() simply calls advanceToNext(), without persisting approval. Consequently "N transactions to review" in NetOverviewSection.vue is the count of ALL transactions in period, not an outstanding queue.
- Dashboard.vue:greetingMessage uses netWorth thresholds to emit "things are looking quite bleak", "Ahh... well in the black", or "Uhh... keep up the... whatever this is." These messages can be misleading and are inappropriate as financial status. User name comes from VITE_USER_ID_PLAID and may display an opaque identifier.
- Persisted Plaid reconnect count is already detected by refreshPersistedConnectionHealth(), but accountReconnectMessage is shown as header prose instead of an actionable item. Dashboard's obsolete useTransactions().loadTransactions(1,{force:true}) fetch remains after embedded transaction panel removal (see completed TP-20261007-003 report).
- frontend/src/components/dashboard/NetOverviewSection.vue: three equal Tier-1 cards; "Needs attention" card and attention highlight are driven by unreviewed-style count that does not exist.

## Required edits (in order)
1. Dashboard.vue + NetOverviewSection.vue: rename reviewCount/reviewCountLabel semantics to periodTransactionCount/transactionCountLabel (or keep internal ref temporarily but NEVER assert "to review"). Present under a calm "Transactions" card: "N transactions in selected period", CTA "Review transactions" opens the existing modal; 0 => "No transactions in this period", no urgent border. Keep optional tag filter. No new reviewed/status persistence or flag by inference.
2. Render real actionable connection warning separately when uniqueReconnectConnections(getAccounts().accounts) > 0: "N connections need reconnection" and router-link to /accounts, using existing accountReconnectMessage or structured count. Only verified reconnect conditions receive attention styling. Keep non-blocking load-failure notice distinct from urgent reconnection; no modal auto-open.
3. Dashboard.vue: replace greetingMessage netWorth-based snark with neutral compact heading "Overview", date and optional factual activityStatusMessage (e.g., subdued status line with clear source). Do not render VITE_USER_ID_PLAID as a human display name. Do not make the welcome heading a second hero.
4. Remove unused useTransactions/pageSize/loadTransactions initial dashboard fetch and its failure branch; remove fetchNetAssets/netWorth solely if no visible metric consumes it. Keep refreshOptions, fetchDashboardActivityStatus, loadSafeToSpend, connection health, and loadReviewCount (renamed) independently robust; preserve race guards. Avoid duplicating review count request from both loadDashboardData and immediate watch unless a dependency requires it.
5. Preserve TP-20261007-003 hierarchy: Safe-to-Spend as primary guidance; true reconnection alert when present; low-key Transactions card; Cash direction with selected date; Daily Net; compact Financial detail; category; account snapshot; explore links. Do not add new heroes, dashboards, charts, or random alerts. On 360px and 1280px widths verify section reading order, keyboard focus, long currency, empty/error/loading states.

## Tests / validation
- frontend/src/views/__tests__/Dashboard.spec.ts and frontend/src/components/dashboard/__tests__/DashboardSections.spec.ts (update stale "N to review" assertions and snapshots).
- Cases: 10 transactions and no reviewed flag => "10 transactions in selected period", NOT "to review"; zero count; API failure != zero; reconnect warning links /accounts with deduplicated item count; no user ID/snark; no obsolete loadTransactions; review modal still opens; category/period drilling intact.
- cd frontend && npm run test -- --run src/views/__tests__/Dashboard.spec.ts src/components/dashboard/__tests__/DashboardSections.spec.ts && npm run lint && npm run build

## Non-goals
Do not add review-persistence DB schema or falsely treat "Approve" as saved status; this would require a separate backend contract packet. Do not redo completed TP-20261007-003 redesign or touch forecast/transaction review internals. Do not rediscover code beyond named paths.

## Acceptance / completion report
- [ ] First screen tells the truth about current data and actual action required.
- [ ] No implied outstanding review queue, bogus person name, or net-worth mood sentence.
- [ ] Redundant dashboard transactions fetch removed; working routes/modal preserved.
- [ ] Mobile and desktop readable without multiple competing hero cards.
Report changed paths, verification, removed requests, visual comparisons (if captured), and deviations.
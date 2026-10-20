# TP-20261019-003: Professional Table System, Totals and Drilldowns

**Packet ID:** TP-20261019-003  
**Status:** Complete  
**Created:** 2026-10-19  
**Last updated:** 2026-10-19  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/completed/TP-20261019-003-professional-tables-and-total-bars.md`  
**Priority:** P1  
**Workstream size:** One independently testable implementation packet  
**Depends on:** TP-20261019-002  
**Series:** Four packets (002 → 003 → 004 → 005), ordered due to shared summary/style contracts.

## Outcome
Make **every canonical HTML table** a coherent professional ledger: clear hierarchy, useful filtered totals/subtotals, consistent density and numeric formatting, visible search/filter state, keyboard/screen-reader support, robust mobile overflow. Consume the all-match financial summary contract from 002. Do not reimplement finance math.

## Confirmed seams on main 360fb21dc5a60d5d7cb93508a214584eba07f1de
- `frontend/src/components/base/BaseTable.vue` hardcodes `divide-gray-200` instead of the Nightfox `--table-*` tokens. `BasePanel.vue` offers multiple border tones, but table consumers also layer independent `.card`, `.table-panel`, `.table-shell`, `border`, `shadow` styles.
- `frontend/src/components/tables/TransactionsTable.vue`, `AccountsTable.vue`, `InstitutionTable.vue`, `MasterTxidTable.vue`, `ModalTransactionsDisplay.vue`, `UpdateTransactionsTable.vue` all author their own table geometry and cells; `PaginationControls.vue` is shared but totals have inconsistent positioning. `InstitutionTable.vue` nests another scrollable table on expansion. `MasterTxidTable.vue` has clickable `th` sort rather than accessible sort button.
- `UpdateTransactionsTable.vue` pads a minimum 12 rows with visually empty placeholders and has nested scroll/virtualization; dense editing controls risk clipping. `ModalTransactionsDisplay.vue` has thick outer padding and redundant borders. `Transactions.vue` has summary/filter controls already, but page-only signed amount is not the all-filtered figure.
- `AccountsTable.vue` has sorting/filter chips but no useful grouped totals by account type; summing all balances into one unqualified number is misleading for assets/liabilities. `InstitutionTable.vue` lists refresh state and nested balances without group summaries.

## Ordered edits
1. **Shared visual contract:** refactor/extend `frontend/src/components/base/BaseTable.vue` (or one narrowly shared CSS utility alongside it) and `frontend/src/assets/css/main.css`, using existing `frontend/src/styles/theme.css` `--table-surface,--table-header,--table-border,--table-hover,--table-control,--font-data`. Define reusable quiet heading, aligned numeric columns (`font-variant-numeric:tabular-nums`), row min-heights, tone for hover/selected/error, sticky header only where scrolling, focus outlines, `overflow-x:auto` **at one owning wrapper**, `min-width:0` responsive grid children. Avoid nested six-sided outlines; use a single containing surface and internal separators. Existing form/virtualization/edit interfaces remain usable.
2. **Transactions Activity:** `frontend/src/views/Transactions.vue` and `frontend/src/components/tables/UpdateTransactionsTable.vue`: compact ledger summary bar above the header or below filters:
   **All matching** N · Economic income $ · Expense $ · Refund $ · Net $, with separate “Movement / unclassified” disclosure, and a quieter **Page subtotal** label for displayed rows only. Show active scope chips and the effective date/account/category/search filters; no second client-side hidden filter. Sorting and pagination preserve global totals. Keep edit, recurring handoff, transfer review, running-balance and CSV behavior unchanged. Do not count virtual spacer/placeholder rows. Optionally keep totals bar sticky within table **without floating over editable fields**.
3. **Account / institution tables:** `frontend/src/components/tables/AccountsTable.vue`, `InstitutionTable.vue`, `frontend/src/views/Accounts.vue`, `frontend/src/views/Institutions.vue`: show filtered account count and **separate assets vs liabilities**, optional net assets **only from type-aware canonical values and matching fresh scope**, with expandable subtotal by account group/institution; never simply add account balances of unlike types or treat credit-card debt as cash. Reuse `frontend/src/utils/accountPortfolio.js` and the existing account portfolio grouping logic instead of a shadow classifier. Hidden accounts explicit; missing/stale balance shows “Unavailable” or as-of scope, never $0. Refresh/connection state is a subdued status not a colored stripe on every row.
4. **Other canonical tables:** `TransactionsTable.vue` (legacy/dashboard consumer), `MasterTxidTable.vue` (editable legacy), `ModalTransactionsDisplay.vue` (day modal), `PaginationControls.vue`: apply shared styling and precise page-only subtotal where the data is local. **Do not** fabricate an all-matching total for modal/day or legacy pages without complete data. Restore proper `<caption>` or labelled region, button-based sortable column headers, `scope=col`, `aria-sort`; modal rows also keyboard selectable and maintain existing `row-click` event. Retain prior `flowChipLabel` and transfer-neutral semantics.
5. **Information hierarchy:** frontload key ID, merchant/description, category, amount and date; secondary institution/account provenance visually quieter; amount right-aligned with +/− and currency consistent. No column disappears silently at narrower breakpoints; permit horizontal scroll with a clear affordance or explicitly disclosed column-view toggle. Sticky columns only if they do not occlude edit or focus. Actions grouped, disabled and destructive controls still confirmed. Empty/loading/error states same height family and a clear Reset filters action.
6. Update `docs/frontend/THEMING_GUIDE.md` and `docs/frontend/PRODUCT_UI_HIERARCHY.md` with canonical table anatomy; leave shared *page panel* system ownership to 004. Do not touch chart semantic rendering.

## Visual/design targets
Dense yet readable: one table boundary per ledger, mostly neutral headers and row separators, meaningful one-level elevation, alternating row colors extremely subtle, comfortable 12–14px minor labels and normal readable financial values, no bright all-over borders, no accent gradient per column, no excessive pill overload. Table summary feels connected to filtered dataset, never another independent hero card. Respect existing Nightfox tone rather than changing themes.

## Validation
- `cd frontend && npm run test -- --run src/components/tables/__tests__/UpdateTransactionsTable.spec.js src/components/tables/__tests__/AccountsTable.spec.js src/components/tables/__tests__/InstitutionTable.spec.js src/components/tables/__tests__/ModalTransactionsDisplay.spec.js src/views/__tests__/Transactions.spec.js src/views/__tests__/Accounts.spec.js src/views/__tests__/Institutions.spec.js && npm run build`; `frontend/cypress/e2e/transactions.cy.js` and `frontend/cypress/e2e/accounts.cy.js` if browser available.
- Test 15/51 page vs filtered totals, sorting/filter reset, hidden-account exclusion, missing liability balances, 1,001-row virtualization, edit focus/keyboard, 390/768/1280px responsive scroll, no nested scroll traps; screenshots at desktop/mobile and verify overflow/no clipping.
- No schema, no banking mutations, no second income classifier, no ungrounded totals. **Owner:** all `components/tables/*.vue`, `BaseTable.vue`, Accounts/Transactions/Institutions view table regions and table-specific CSS only. 004 owns global panel/surface roles.


## Execution and closeout
Follow `AGENTS.md` and `docs/task-packets/README.md`: pause `scripts/dev-watcher.sh` only if running, preserve unrelated dirty files; inspect only named seams, mark packet/TRACKER In Progress, implement focused scope and tests, then mark Complete/move to completed and update INDEX/TRACKER in the same committed change. Sync/push `origin/main` without force, resume watcher if paused. Provide exact `Workstream`, status, commit link, changed files, totals/visual acceptance evidence, executed commands/results, unrun checks and blockers. Do not mark a failing or unverified test as passed.

# TP-20261016-008: Accounts Overview Hierarchy, Width, Period and Connection Styling

**Packet ID:** TP-20261016-008  
**Status:** Complete  
**Created:** 2026-10-16  
**Last updated:** 2026-10-17
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/completed/TP-20261016-008-accounts-command-center-hierarchy.md`  
**Workstream size:** One targeted implementation packet  
**Priority:** P2  
**Depends on:** TP-20261016-007  
**Series:** 11 packets (TP-20261016-001..011); assume each named prerequisite has landed before starting this packet.  

## Objective
Accounts Overview Hierarchy, Width, Period and Connection Styling. Complete only the named workstream; no broad rediscovery.

## Do not rediscover: exact file/ownership map
- `frontend/src/views/Accounts.vue`
- `frontend/src/components/accounts/AccountPortfolioOverview.vue`
- `frontend/src/components/accounts/AccountPortfolioList.vue`
- `frontend/src/components/accounts/LinkedAccountsSection.vue`
- `frontend/src/components/forms/AccountActionsSidebar.vue`
- `frontend/src/components/layout/TabbedPageLayout.vue (reuse, do not broad-edit)`
- `frontend/src/views/__tests__/Accounts.spec.js`
- `frontend/src/components/accounts/__tests__/AccountPortfolio.spec.js`
- `frontend/src/components/accounts/__tests__/LinkedAccountsSection.spec.js`

## Confirmed current seam (main at authoring 437bdd9cda1bd21d651e7c0ecd24c205d76b6ebc)
Screenshot: main overview occupies left pane while always-visible right `New Account` sidebar reserves large blank area; most sections visually use same dark-blue surfaces. 11/28 linked with hidden exclusions, partial utilization, reconnect banner competes with primary KPI. `Accounts.vue` places `Period` below portfolio yet it only controls subsequent analysis. `LinkedAccountsSection.vue` nested institution/account cards still have `bg-surface-50`, `bg-white`, Tailwind `dark:` and amber hardcodes incompatible with `data-theme` palette; Rewards section open by default.

## Required code edits, in order
1. `Accounts.vue` change Overview layout to full-width for primary portfolio and ledger; place link-account CTA in overview header or compact action bar, keep Sidebar only for Activity/Connections or stack below main at <=1280; preserve all sidebar actions. Put portfolio KPIs first, explicit coverage line next, account filters/ledger next. Move Period selector inside `Most Active`/historical analysis header with its dates and scope label; no false global filter. Distinguish search/account selector and `All accounts` selection, accessible focus states.
2. `AccountPortfolioOverview.vue`: 4 KPIs stay, but visual emphasis net-position/debt exposure and coverage warning; use theme semantic foregrounds (positive teal, negative coral, caution amber) only for true financial meaning. Reduce repetitious borders/glows on nested cards, boost primary numbers to 1.25-1.5rem, preserve tabular digits and ~0.875rem meaningful labels. No arbitrary colors on all headings.
3. `AccountPortfolioList.vue` sharpen institution > account > primary amount > secondary limit/sync/APR, less all-caps 0.72rem critical metadata, column widths minmax(0,1fr), mobile row display stacking at 390px, long institution names safely wrap. Filters remain clear but lighter-weight than account results. Keep full tooltip / accessible label for truncated merchants.
4. `LinkedAccountsSection.vue`: replace institution wrapper `bg-surface-50 ... dark:bg-surface-900` and account wrapper `bg-white ... dark:bg-surface-800` with `background:var(--surface-1/2)` or actual repo tokens from theme.css; replace Tailwind dark variants and amber hardcodes with semantic status surfaces. Reconnect callout separate from individual grouped cards, accordions default closed for Promotions/advanced; top summary linked institution count & needs reconnect; ensure no 3-level border nesting. Check scoped `<style>` theme bindings. Keep Plaid Link execution unchanged.
5. Verify 390/768/1280/1440 screenshots Nightfox/Everforest, sidebar action reachable, overlay focus/contrast with reconnect, long institution names, hidden-account warning not cropped.

## Exact contracts and acceptance fixtures
- Primary portfolio uses available content width rather than dead right gutter; period visually attached to analysis; account group and totals still identical to 007.
- In Nightfox no white account card; in Everforest no dark-on-dark warning; no duplicated link button or zombie sidebar.

## Validation commands
`cd frontend && npm run test -- --run src/views/__tests__/Accounts.spec.js src/components/accounts/__tests__/AccountPortfolio.spec.js src/components/accounts/__tests__/LinkedAccountsSection.spec.js && npm run lint && npm run build`; browser 390/1280 two themes.

## Non-goals
No new banking data, no accounts API refactor, no new chart features; preserve responsive routes and existing cards.

## Implementation/handoff
Read `AGENTS.md`, `docs/task-packets/README.md`, `INDEX.md`, `TRACKER.md`; validate only named symbols against latest main. Set In Progress in tracker before coding. Treat prerequisite packets as implemented, do not re-implement their features. Run focused tests then lint/build; commit only this workstream to main without force, mark Complete, move this packet to completed and update INDEX/TRACKER atomically. Report changed files, test output, fixture/behavior evidence, and deviations. If principal is not trusted, fail closed on new owner-scoped endpoints, not permissive fallback. Do not use Plaid Enrich/new billable APIs.

## Completion report (2026-10-17)

- `Accounts.vue`: the actions sidebar is rendered only on **Activity** and **Connections**; Overview and Trends use the full content width (no dead right gutter). The same link/token actions (`AccountActionsSidebar`, unchanged, Plaid Link untouched) live in a compact, closed-by-default "+ Link an account" panel above the overview, so nothing is duplicated and every action stays reachable. Order is KPIs, coverage line, filters and ledger, then the analysis. The **Period** control moved into an "Activity & history" header that says what it controls (history, money movement, most-active) and that it does not change the balances above; test ids `accounts-period-bar`, `history-range-select`, `accounts-period-dates` are preserved. The reconnect banner is now a quiet amber line instead of a red 4px alarm competing with the headline numbers.
- `AccountPortfolioOverview.vue`: borderless KPI tiles on one surface, net position emphasised (1.5rem, accent edge) over the other KPIs (1.25rem), liabilities in the negative colour, partial-coverage and unknown-balance notes in a caution surface; labels 0.875rem; tabular digits preserved.
- `AccountPortfolioList.vue`: group > institution (1rem, no longer all-caps 0.78rem) > account (1rem) > primary amount (1.15rem) > secondary details (0.875rem); hairline dividers instead of repeated borders; long names wrap; at <=480px each row stacks identity / amount / details in one column; filter labels lighter than results.
- `LinkedAccountsSection.vue`: every `bg-white`, `bg-surface-*`, `border-surface-*`, `dark:` and `amber-*` class replaced with theme tokens (`--surface-1/2`, `--divider`, `--color-warning`); at most two levels of surface (Card > institution fill > hairline-separated account rows); reconnect callout and badge use caution tokens; Rewards & Promotions is closed by default; a summary line ("8 institutions linked · 1 needs reconnect"); `text-muted-foreground` and 0.72rem all-caps labels replaced by `text-muted` at 0.875rem.
- **Browser verification (headless Chrome over CDP, real data via an isolated backend on :5001, not your :5000 server):** 1280px and 390px in Nightfox and Everforest Light for Overview, and 1280px for Connections. No horizontal overflow at either width (scrollWidth equals clientWidth), no white card in Nightfox, the amber warning is legible in Everforest, the sidebar appears on Connections only, "11 visible of 28 linked; 17 hidden excluded" and "Known credit limits: 2/5 cards" render. 768px and 1440px were not captured separately.
- Tests: `Accounts.spec.js` (34: no sidebar on Overview, sidebar on Activity/Connections, none on Trends, single link panel, period attached to analysis and ordered after the ledger), `AccountPortfolio.spec.js`, `LinkedAccountsSection.spec.js` all pass. `npm run build` passes; ESLint 0 errors. Full frontend run: 495 pass, the same 36 unrelated Dashboard / ChartRoutePage / DashboardSections / ForecastChart failures as before this packet.
- Note for you: your Flask dev server on :5000 (started 00:29) predates the TP-007 sign fix and the new migrations, so it still serves the old (wrong-sign) Robinhood card balance. Restart it to pick up the changes.

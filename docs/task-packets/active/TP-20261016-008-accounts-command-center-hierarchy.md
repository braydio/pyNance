# TP-20261016-008: Accounts Overview Hierarchy, Width, Period and Connection Styling

**Packet ID:** TP-20261016-008  
**Status:** Ready  
**Created:** 2026-10-16  
**Last updated:** 2026-10-16  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/active/TP-20261016-008-accounts-command-center-hierarchy.md`  
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

# TP-20261014-020: Investments Filter, Holdings and Expandable Rows

**Packet ID:** TP-20261014-020  
**Status:** Complete  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** docs/task-packets/completed/TP-20261014-020-investments-filter-holdings-ui.md  
**Depends on:** TP-20261014-010, TP-20261014-011, TP-20261014-012, TP-20261014-014  
**Priority:** Normal  
**Workstream size:** One focused UI packet  
**Source audit:** docs/frontend/UI_FIELD_AUDIT_2026-10-14.md

## Exact file paths
- frontend/src/views/Investments.vue
- frontend/src/components/charts/PortfolioAllocationChart.vue
- frontend/src/components/forms/LinkProviderLauncher.vue

## Confirmed current state
Investments CSS uses hardcoded #6b7280 metric/controls text and #fff on refresh button; holdings uses six-column faux table with button expandable account row; Transactions filters native details and 6 fields; maintenance appears after charts.

## Required implementation
Replace fixed text/button colors with semantic palette contrast and shared input/select sizing. Establish portfolio summary > Holdings + institution/account toolbar > performance > transaction filters/pagination > subdued connection maintenance. Holding account buttons aria-expanded plus aria-controls matching detail; keyboard focus and full text for long securities, right-aligned prices/qty, local table scroll rather than whole page overflow. Section subnav scroll-margin below nav, active focus. Filter disclosure visible count and reset with responsive 320px fields.

## Validation
Investments.spec.js, frontend/src/api/__tests__/investments.spec.js, PortfolioAllocationChart.cy.js; expanded long holdings, filters and two themes at 320/1280, keyboard; lint/build.

## Non-goals
No portfolio calculation or link scope change.

## Completion contract
Check AGENTS.md and docs/task-packets/README.md, TRACKER and INDEX; validate named paths only. Mark In Progress, implement ordered fixes, run focused tests and lint/build. After completion move packet to completed/, update INDEX/TRACKER atomically, commit to origin/main without force. Report files, browser validation vs static assumptions, exact commands/output and deviations. Coordinate overlapping files with prerequisite packets; no broad refactor.

## Completion report

- `Investments.vue`: hardcoded `#6b7280`/`#94a3b8` text and the `#fff`-on-cyan button replaced with semantic tokens (`--text-muted`, `--accent-primary` / `--accent-primary-contrast`); filter, date and select fields use the shared `.input`/`.select` geometry; order is Portfolio summary > Holdings + institution/account toolbar > Performance > Activity (filters + pagination) > subdued Manage section (unchanged, verified). Holding account buttons now expose string `aria-expanded` and `aria-controls` that match the detail panel id; long security names wrap (full text also in `title`) instead of clipping; qty/price/value stay right-aligned with tabular figures; holdings and transactions tables scroll inside focusable labelled regions (`role="region"`, `tabindex=0`) with a 40rem row minimum instead of overflowing the page. Section sub-nav targets have `scroll-margin-top: 5rem`, are focusable (`tabindex=-1`) and receive focus after the nav scroll. The transaction-filter disclosure keeps the visible `(count)` (with a descriptive `title`), gets a responsive auto-fit grid for 320px and a "Reset filters" button; pager/refresh buttons are `type="button"`.
- **Bug fixed:** `LinkProviderLauncher` is a renderless slot component and Investments never supplied slot content, so "Link New Investments Account" showed a heading with no button. Investments now renders a real button (`data-testid="link-investments"`) plus Plaid status/error messages from the slot props. `LinkProviderLauncher.vue` itself needed no change; link scopes are unchanged (`['investments']`).
- `PortfolioAllocationChart.vue`: empty state when there is no allocation data, `role="img"` + descriptive `aria-label` and a screen-reader list of values, `maintainAspectRatio: false` so it fits its 280px wrapper.
- Tests: `Investments.spec.js` (+5), new `PortfolioAllocationChartStates.spec.js` (2); existing Investments/API tests pass. Full vitest 73 files / 470 tests, lint 0 errors, build OK.
- Not run: `PortfolioAllocationChart.cy.js` (Cypress) and the 320/1280 two-theme browser pass with long holdings expanded. `src/api/__tests__/investments.spec.js` ran as part of the full vitest suite.

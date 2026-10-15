# TP-20261014-020: Investments Filter, Holdings and Expandable Rows

**Packet ID:** TP-20261014-020  
**Status:** Ready  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** docs/task-packets/active/TP-20261014-020-investments-filter-holdings-ui.md  
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

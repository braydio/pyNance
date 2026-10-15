# TP-20261014-022: Every Route Visual and Keyboard QA Gate

**Packet ID:** TP-20261014-022  
**Status:** Ready  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** docs/task-packets/active/TP-20261014-022-full-route-visual-regression.md  
**Depends on:** TP-20261014-010 through TP-20261014-021  
**Priority:** High  
**Workstream size:** One focused UI packet  
**Source audit:** docs/frontend/UI_FIELD_AUDIT_2026-10-14.md

## Exact file paths
- frontend/src/router/index.js
- frontend/cypress/e2e/ui-visual-regression.cy.js
- docs/frontend/UI_FIELD_AUDIT_2026-10-14.md

## Confirmed current state
Static review covers 14 registered routes but cannot certify actual pixel overlap/clipping/focus without browser. Cypress exists in frontend/package.json.

## Required implementation
Add Cypress e2e matrix for /, /accounts, /transactions, /forecast, /planning, /settings, /charts/cashflow, /charts/category, /charts/assets/year-comparison, /investments, /rsa-monitor, /institutions, /accounts/table, /summary. Both themes widths 320x568,390x844,768x1024,1280x800,1440x900 and 200% zoom/text simulation. For each route open all representative dropdowns/expandables/menus/modals, test long values and loading/empty/error via controlled fixtures. Assert document scrollWidth <= clientWidth+1 except intentional local table/log scroll, active popup inside viewport/not clipped by ancestor, dialog focus/return, semantic keyboard control/aria state, visible selected options, sampled computed contrast. Screenshot evidentiary states; update audit doc PASS/FAIL/BLOCKED per route. Do not claim browser verification when unavailable; document blocker and manual checklist.

## Validation
cd frontend && npm run lint && npm run build && npm run test -- --run; npm run test:e2e in configured backend/fixture environment. Preserve screenshots locally unless repo policy wants capture; include before/after paths/results.

## Non-goals
No speculative redesign beyond observed failures.

## Completion contract
Check AGENTS.md and docs/task-packets/README.md, TRACKER and INDEX; validate named paths only. Mark In Progress, implement ordered fixes, run focused tests and lint/build. After completion move packet to completed/, update INDEX/TRACKER atomically, commit to origin/main without force. Report files, browser validation vs static assumptions, exact commands/output and deviations. Coordinate overlapping files with prerequisite packets; no broad refactor.

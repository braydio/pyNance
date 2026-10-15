# TP-20261014-013: Modal Overlay Focus, Stacking and Scroll

**Packet ID:** TP-20261014-013  
**Status:** Ready  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** docs/task-packets/active/TP-20261014-013-modal-viewport-focus.md  
**Depends on:** TP-20261014-010, TP-20261014-011  
**Priority:** High  
**Workstream size:** One focused UI packet  
**Source audit:** docs/frontend/UI_FIELD_AUDIT_2026-10-14.md

## Exact file paths
- frontend/src/components/ui/Modal.vue
- frontend/src/components/forms/LinkAccount.vue
- frontend/src/components/transactions/TransactionReviewModal.vue
- frontend/src/components/modals/TransactionModal.vue
- frontend/src/components/forecast/ForecastLayout.vue
- frontend/src/components/tables/AccountsTable.vue

## Confirmed current state
Modal.vue is v-if=true, fixed backdrop, w-auto mt-20, close text-gray-500 hover:text-black; lacks dialog role, Escape, focus trap/return, body scroll lock. AccountsTable uses it for destructive delete. Other dialogs use independent implementations; TransactionReviewModal has global window keydown and nested rule confirmation.

## Required implementation
Modal.vue Teleport body, role dialog aria-modal + stable title ID, close button type=button; Escape/focus trap/return and body lock when mounted; sized width:min(100%, configured), max-height calc(100dvh - 2rem), scroll body region, action footer visible. Preserve title/body slots and backdrop self click. Review modal global shortcut handler must ignore hidden modal, text-entry and nested rule dialog; don't advance on unintentionally focused arrow keys. Check LinkAccount's existing teleport/focus and ForecastLayout source modal for long content, collision, mobile keyboard; keep workflows intact.

## Validation
New frontend/src/components/ui/__tests__/Modal.spec.js; TransactionReviewModal.spec.js, TransactionModal.spec.js, LinkAccount.cy.js; test 320x568, zoom, Escape, outside click, focus return, nested confirm, scrolling footer; lint/build.

## Non-goals
No changes to review approval persistence, Plaid Link or delete business flow.

## Completion contract
Check AGENTS.md and docs/task-packets/README.md, TRACKER and INDEX; validate named paths only. Mark In Progress, implement ordered fixes, run focused tests and lint/build. After completion move packet to completed/, update INDEX/TRACKER atomically, commit to origin/main without force. Report files, browser validation vs static assumptions, exact commands/output and deviations. Coordinate overlapping files with prerequisite packets; no broad refactor.

# TP-20261014-013: Modal Overlay Focus, Stacking and Scroll

**Packet ID:** TP-20261014-013  
**Status:** Complete  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** docs/task-packets/completed/TP-20261014-013-modal-viewport-focus.md  
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

## Completion report

- New `composables/useModalA11y.js`: reference-counted body scroll lock, focus moved into the dialog, Tab trap, Escape handled by the top-most dialog only (callback returns true when handled), and focus returned to the opener on close.
- `ui/Modal.vue`: teleported to `<body>`, `role="dialog"` + `aria-modal` + `aria-labelledby` (stable `useId` title id), close button `type="button"` with a label and themed colors (was `text-gray-500 hover:text-black`), width `min(100%, size)`, `max-height: calc(100dvh - 2rem)`, scrolling body region and an optional always-visible `footer` slot, backdrop self-click preserved, reduced-motion. The delete flow in `AccountsTable.vue` keeps working unchanged (title/body slots).
- `TransactionReviewModal.vue`: focus trap/scroll lock/Escape for the dialog and separately for the nested "Save rule" confirmation (Escape there means "skip rule"); the global key handler now ignores keys while hidden or while the rule prompt is open, no longer treats typed `0`, `n` or `1-5` in a field as shortcuts (previously typing "0" in an amount closed the modal), and ignores arrow shortcuts from a focused button/link or with Ctrl/Meta/Alt. Review/approval behavior is unchanged.
- `TransactionModal.vue`: same composable (replaces the focus-dependent `keyup.esc`), dialog max-height `100dvh - 2rem` with scrolling content, close button `type="button"`.
- `ForecastLayout.vue` source modal: composable, `tabindex="-1"`, `max-height: calc(100dvh - 2rem)`. `LinkAccount.vue` reviewed: it already teleports and implements its own focus trap/return/scroll lock; left unchanged.
- Tests: new `components/ui/__tests__/Modal.spec.js` (6) and three new keyboard/scroll cases in `TransactionReviewModal.spec.js`; `TransactionModal.spec.js` passes. Full vitest 60 files / 404 tests, lint 0 errors, build OK.
- Not run: `LinkAccount.cy.js` and 320x568/zoom browser checks (no browser run here).

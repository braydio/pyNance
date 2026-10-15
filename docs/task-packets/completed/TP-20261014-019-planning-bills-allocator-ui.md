# TP-20261014-019: Planning Bill Entry, List and Allocation Controls

**Packet ID:** TP-20261014-019  
**Status:** Complete  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** docs/task-packets/completed/TP-20261014-019-planning-bills-allocator-ui.md  
**Depends on:** TP-20261014-010, TP-20261014-011, TP-20261014-014  
**Priority:** Normal  
**Workstream size:** One focused UI packet  
**Source audit:** docs/frontend/UI_FIELD_AUDIT_2026-10-14.md

## Exact file paths
- frontend/src/views/Planning.vue
- frontend/src/components/planning/PlanningSummary.vue
- frontend/src/components/planning/BillForm.vue
- frontend/src/components/planning/BillList.vue
- frontend/src/components/planning/Allocator.vue

## Confirmed current state
BillForm custom CSS for name/amount/date/frequency/category and inline error; BillList clickable rows with nested Edit/Delete; Allocator numeric inputs and remainder alert; multiple p-6 Cards add depth.

## Required implementation
BillForm group aligned semantic fields, 1 column mobile/2 wider, visible required fields, aria-invalid/describedby, currency indicator/preview, clear error and Save disabled rationale; preserve validation. BillList chronological due scan (only if supported), explain predicted source badge, long names wrap, keyboard row expand, separate edit/delete actions with confirm. Allocator aligned numeric/currency columns and live remainder next to Save, no horizontal spill; Summary key state above add/edit form. Preserve 40+px targets.

## Validation
BillForm.spec.ts, Allocator.spec.ts, PlanningSummary.spec.ts, Planning.spec.js, Planning.cy.js if existing; 320 and 1280 light/dark with validation/edit/empty; lint/build.

## Non-goals
No recurrence/allocator algorithm or payments change.

## Completion contract
Check AGENTS.md and docs/task-packets/README.md, TRACKER and INDEX; validate named paths only. Mark In Progress, implement ordered fixes, run focused tests and lint/build. After completion move packet to completed/, update INDEX/TRACKER atomically, commit to origin/main without force. Report files, browser validation vs static assumptions, exact commands/output and deviations. Coordinate overlapping files with prerequisite packets; no broad refactor.

## Completion report

- `BillForm.vue`: required fields marked (visible `*` plus a "required" note and `aria-required`); `aria-invalid` and `aria-describedby` link each input to its error (`role="alert"`), the amount preview stays associated with the amount field; Save keeps its existing validity gating and now explains why it is unavailable ("Add bill is unavailable until you fix: amount..."); controls use the shared control-height, 1rem input text, contrast-verified error color and focus ring; 1 column on phones / 2 columns from 640px unchanged. Validation rules and payload are untouched.
- `BillList.vue`: soonest-due-first order kept; each row's main button now toggles an `aria-expanded`/`aria-controls` details region (category, and what "Predicted" means) and still emits `select`; the Predicted badge has an explanatory `title`; Edit and Delete are separate 40px controls with per-bill accessible names, and Delete asks for inline confirmation before emitting `delete`; long names wrap; amounts are tabular; hardcoded slate/white colors replaced with theme tokens.
- `Allocator.vue`: each category row is an aligned grid of name / slider / percent number field / currency amount (two-line grid on phones, one line from 640px, no horizontal spill); sliders and number fields share the same clamping handler; the total/remaining summary is a polite live region that also shows the unassigned currency amount and uses contrast-verified colors. `PlanningSummary.vue` (already above the form in `Planning.vue`) uses theme tokens, tabular figures and >= 0.875rem helper text. Allocation math, recurrence and persistence are unchanged.
- Tests: `BillForm.spec.ts` (+2), `Allocator.spec.ts` (+2), new `BillList.spec.ts` (4); `PlanningSummary.spec.ts` and `Planning.spec.js` pass. Full vitest 72 files / 463 tests, lint 0 errors, build OK.
- Not run: `Planning.cy.js` (no such file exists), `vue-tsc` (the installed binary fails to start with ERR_PACKAGE_PATH_NOT_EXPORTED on this Node version), and the 320/1280 two-theme browser pass.

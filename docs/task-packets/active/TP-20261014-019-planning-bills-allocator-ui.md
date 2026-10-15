# TP-20261014-019: Planning Bill Entry, List and Allocation Controls

**Packet ID:** TP-20261014-019  
**Status:** Ready  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** docs/task-packets/active/TP-20261014-019-planning-bills-allocator-ui.md  
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

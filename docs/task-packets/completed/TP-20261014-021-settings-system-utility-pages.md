# TP-20261014-021: Settings, RSA Monitor and Utility Page Polishing

**Packet ID:** TP-20261014-021  
**Status:** Complete  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** docs/task-packets/completed/TP-20261014-021-settings-system-utility-pages.md  
**Depends on:** TP-20261014-010, TP-20261014-011, TP-20261014-013, TP-20261014-014  
**Priority:** Normal  
**Workstream size:** One focused UI packet  
**Source audit:** docs/frontend/UI_FIELD_AUDIT_2026-10-14.md

## Exact file paths
- frontend/src/views/Settings.vue
- frontend/src/views/RsaMonitor.vue
- frontend/src/views/Institutions.vue
- frontend/src/router/index.js
- frontend/src/components/widgets/RefreshPlaidControls.vue

## Confirmed current state
Settings has appearance, AI message/LLM URL Save, connected refresh, advanced commands details with template/argument and pre output. RSA monitor order table, broker list, logs with 22rem max-height and .78rem text.

## Required implementation
Settings appearance/connections prioritized, AI config secondary and advanced local commands collapsed by default. Clear Save/Refresh result and aria-live, constrained URL/pre output overflow with copy where supported, no hidden action behind expanding details. RsaMonitor status chips semantic and legible, contained order table x-scroll, broker names wrap, log region bounded with timestamps/readable >.8125rem metadata, clear Refresh/last updated/failure. Keep institution page nesting owned by 014/017, no privileged menu leak.

## Validation
Settings.spec.js, new RsaMonitor.spec.js, 320/390/1280 light/dark, long logs, empty/error, advanced open; lint/build.

## Non-goals
No backend commands changes, no expanding access to operator tools.

## Completion contract
Check AGENTS.md and docs/task-packets/README.md, TRACKER and INDEX; validate named paths only. Mark In Progress, implement ordered fixes, run focused tests and lint/build. After completion move packet to completed/, update INDEX/TRACKER atomically, commit to origin/main without force. Report files, browser validation vs static assumptions, exact commands/output and deviations. Coordinate overlapping files with prerequisite packets; no broad refactor.

## Completion report

- `Settings.vue`: order is now Appearance > Connected Accounts > Dashboard AI message > collapsed "Advanced: local commands". **Restored a broken feature:** the template bound `executeCommand`, `commandCanSubmit`, `commandLoading`, `commandFeedback` and `commandOutput`, but a prior refactor (771286a22) dropped their script, so "Run command" did nothing. They are back with the original behavior (POST `/api/codex/exec` with `{preset, task}`; backend untouched, no new access). Save/Run feedback has `role="status"`/`"alert"` + `aria-live="polite"` with themed success/error colors; command output is a bounded (`max-height: 18rem`), focusable, wrapping `<pre>` with a Copy output button (Clipboard API, "Copied"/"Copy failed" state); the LLM URL field is wider and described by its help text; small help text >= 0.875rem.
- `RsaMonitor.vue`: status pills use the contrast-verified text roles instead of hardcoded pastel hexes and the overall chip has an `aria-label`; Refresh shows `Refreshing…` with `aria-busy`; errors are `role="alert"` and say that the last successful check is still shown; loading and empty states; the orders table lives in a focusable labelled scroll region with `scope="col"` headers and right-aligned quantities; broker names wrap instead of ellipsizing; each log `<pre>` is a labelled, focusable region (still `max-height: 22rem`) with metadata/log text >= 0.8125/0.875rem and monospace.
- `RefreshPlaidControls.vue`: start/end date inputs have accessible names; the account menu button reports `aria-expanded`/`aria-controls`, closes on Escape, and its label reflects the selection ("All linked accounts" / "N accounts selected"); `RefreshPlaidControls.cy.js` text updated to match. `Institutions.vue` / `router/index.js` needed no change here (nesting fixed in TP-014; no new operator routes or menus were added).
- Tests: `Settings.spec.js` (+5 including the restored command flows), new `RsaMonitor.spec.js` (5). Full vitest 74 files / 480 tests, lint 0 errors, build OK.
- Not run: Cypress, and the 320/390/1280 two-theme browser pass with long logs and Advanced open.

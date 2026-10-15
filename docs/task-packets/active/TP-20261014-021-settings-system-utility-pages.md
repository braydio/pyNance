# TP-20261014-021: Settings, RSA Monitor and Utility Page Polishing

**Packet ID:** TP-20261014-021  
**Status:** Ready  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** docs/task-packets/active/TP-20261014-021-settings-system-utility-pages.md  
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

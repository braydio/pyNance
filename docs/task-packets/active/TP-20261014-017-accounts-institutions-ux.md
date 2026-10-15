# TP-20261014-017: Accounts, Institutions and Account Selection UX

**Packet ID:** TP-20261014-017  
**Status:** Ready  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** docs/task-packets/active/TP-20261014-017-accounts-institutions-ux.md  
**Depends on:** TP-20261014-010, TP-20261014-011, TP-20261014-013, TP-20261014-014, TP-20261014-008, TP-20261014-009  
**Priority:** High  
**Workstream size:** One focused UI packet  
**Source audit:** docs/frontend/UI_FIELD_AUDIT_2026-10-14.md

## Exact file paths
- frontend/src/views/Accounts.vue
- frontend/src/components/accounts/LinkedAccountsSection.vue
- frontend/src/components/tables/AccountsTable.vue
- frontend/src/components/tables/InstitutionTable.vue
- frontend/src/components/ui/AccountSelector.vue
- frontend/src/components/widgets/TopAccountSnapshot.vue
- frontend/src/views/Institutions.vue

## Confirmed current state
Accounts feature changes TP-005..009 still active. InstitutionTable click-on-tr expansion lacks native keyboard button/aria-expanded; nested table no local overflow. AccountSelector clickable div cards have no keyboard selection. AccountsTable multiselect type control, hidden/delete options, table/modal need better separation.

## Required implementation
AFTER TP-008/009: tidy Accounts type chips/ledger, selection, account details and reconnect without recalculating new APR/limits. Long names/masks wrap and fields match shared sizing. InstitutionTable use expand button inside cell with aria-expanded/controls, nested overflow-x:auto table, refresh progress/error and click.stop; avoid duplicate Institutions BasePageLayout (owned 014). AccountSelector use checkbox/label or button aria-pressed keyboard and classification by account type (not balance sign). AccountsTable type filter usable multi-select/checkbox list, clear filter chips/keyboard sort, destructive Hide/Delete gated in management mode; share modal packet 013. LinkedAccountsSection collapsed empty promo area, legible institution sections and rate only if supported.

## Validation
Accounts.spec.js, LinkedAccountsSection.spec.js, frontend/cypress/e2e/accounts.cy.js and new InstitutionTable/AccountSelector keyboard tests. Browser 320/1280 hidden/type-filter/expanded institution/deletion/reconnect, light/dark; lint/build.

## Non-goals
No duplicate data work from TP-005..009 or banking ingestion changes.

## Completion contract
Check AGENTS.md and docs/task-packets/README.md, TRACKER and INDEX; validate named paths only. Mark In Progress, implement ordered fixes, run focused tests and lint/build. After completion move packet to completed/, update INDEX/TRACKER atomically, commit to origin/main without force. Report files, browser validation vs static assumptions, exact commands/output and deviations. Coordinate overlapping files with prerequisite packets; no broad refactor.

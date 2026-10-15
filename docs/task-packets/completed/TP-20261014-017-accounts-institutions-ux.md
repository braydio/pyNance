# TP-20261014-017: Accounts, Institutions and Account Selection UX

**Packet ID:** TP-20261014-017  
**Status:** Complete  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** docs/task-packets/completed/TP-20261014-017-accounts-institutions-ux.md  
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

## Completion report

- `InstitutionTable.vue`: expansion is a real button in the institution cell (`aria-expanded`, `aria-controls`) instead of a clickable `<tr>`; the nested accounts table sits in its own `overflow-x: auto` region; per-institution Refresh shows a busy state, a per-row error and does not toggle the row; loading, empty and retryable load-error states; long account names wrap.
- `AccountSelector.vue`: account cards are `<label>`s wrapping a real checkbox (keyboard + screen reader operable, visible `:focus-within` ring); asset/liability is derived from account type via the shared classifier rather than the sign of the balance; quick actions are `type="button"`; long names wrap.
- `AccountsTable.vue`: multi-select `<select>` replaced by a checkbox fieldset with a Clear action and removable filter chips (with accessible labels); sortable headers are buttons with `aria-sort`; "Include hidden" and "Filter types" have pressed/expanded state; Hide/Delete live behind "Manage accounts" and Delete additionally needs "Enable delete", which re-locks when leaving management mode; load errors show a retry; the delete confirmation uses the shared `Modal` from TP-013.
- `LinkedAccountsSection.vue`: long names wrap (the empty promotions disclosure and unsupported-APR handling were already done in TP-008). `Accounts.vue` and `TopAccountSnapshot.vue` needed no further change here (the ledger/type chips/reconnect were done in TP-008/009 and snapshot label sizes in TP-015); `Institutions.vue` double-wrapper was fixed in TP-014.
- Tests: new `InstitutionTable.spec.js`, `AccountSelector.spec.js`, `AccountsTable.spec.js` (17 total cases); full vitest 70 files / 448 tests, lint 0 errors, build OK.
- Not run: `accounts.cy.js` (does not exist in `cypress/e2e/`) and the 320/1280 browser pass for hidden/type-filter/expanded/delete/reconnect states.

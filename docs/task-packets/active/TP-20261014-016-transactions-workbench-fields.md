# TP-20261014-016: Transactions Data Grid, Filters and Import

**Packet ID:** TP-20261014-016  
**Status:** Ready  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** docs/task-packets/active/TP-20261014-016-transactions-workbench-fields.md  
**Depends on:** TP-20261014-010, TP-20261014-011, TP-20261014-012, TP-20261014-013  
**Priority:** High  
**Workstream size:** One focused UI packet  
**Source audit:** docs/frontend/UI_FIELD_AUDIT_2026-10-14.md

## Exact file paths
- frontend/src/views/Transactions.vue
- frontend/src/components/tables/UpdateTransactionsTable.vue
- frontend/src/components/AccountFilter.vue
- frontend/src/components/TypeSelector.vue
- frontend/src/components/forms/ImportFileSelector.vue
- frontend/src/components/recurring/RecurringTransactionSection.vue
- frontend/src/components/transactions/InternalTransferScanner.vue

## Confirmed current state
UpdateTransactionsTable has 10 fixed-width columns, outer overflow-hidden, inner min-h 50vh/max-h 70vh and all cells ellipsis; sorting on th click without keyboard button. Transactions top bar packs search, Filter, Import, date/account/type and chips.

## Required implementation
Replace clickable table headers with button inside th and aria-sort while preserving sortBy and virtualization. Right align amounts/tabular digits. Default column priority date/description/amount/category/account/actions; secondary hide via column chooser or expanded row accessible at narrow width. Table-only horizontal scroll, avoid hiding Save/Cancel/amount via ellipsis and nested overflow; no 50vh minimum when few rows. Search dedicated row mobile with Filter/Import/Clear below; filter chips wrap and import panel scrolls safely. Standardize edit fields/labels, category selector, recurring and transfer confirmation focus/colors.

## Validation
UpdateTransactionsTable.spec.js, Transactions.spec.js, frontend/cypress/e2e/transactions.cy.js. Browser 320px import/filter/long merchant/edit far-right, keyboard sort, zoom; lint/build.

## Non-goals
No transaction API or financial business changes.

## Completion contract
Check AGENTS.md and docs/task-packets/README.md, TRACKER and INDEX; validate named paths only. Mark In Progress, implement ordered fixes, run focused tests and lint/build. After completion move packet to completed/, update INDEX/TRACKER atomically, commit to origin/main without force. Report files, browser validation vs static assumptions, exact commands/output and deviations. Coordinate overlapping files with prerequisite packets; no broad refactor.

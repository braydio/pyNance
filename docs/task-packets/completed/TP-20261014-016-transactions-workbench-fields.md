# TP-20261014-016: Transactions Data Grid, Filters and Import

**Packet ID:** TP-20261014-016  
**Status:** Complete  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** docs/task-packets/completed/TP-20261014-016-transactions-workbench-fields.md  
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

## Completion report

- `UpdateTransactionsTable.vue`: sortable headers are real `<button>`s inside `<th scope="col" aria-sort>` (none/ascending/descending), driven by a column config; sorting (`sortBy`) and row virtualization are unchanged (colspan now follows the visible column count). Date, Amount, Description, Category, Merchant, Account and Actions show by default; Institution, Subtype and Running balance are opt-in via a "Columns" chooser. Amount column right-aligned with tabular numerals. Ellipsis moved from whole cells to text spans (with `title` for the full value) so Save/Cancel, option toggles and edit inputs are never clipped; the 50vh/55vh minimum and `overflow-hidden` shell are gone, the grid scrolls horizontally only inside a focusable labelled region with a 56rem minimum. Edit inputs have accessible names, all buttons are `type="button"`, small labels raised to >= 0.8125/0.875rem, local `.input` override removed so shared control geometry applies, category selects wrap.
- `Transactions.vue`: search owns its own row below 640px with Filters / Import / Clear beneath; new toolbar Clear resets search and filters together; import panel bounded (`min(24rem, 60dvh)`, scrolls); pills raised to `text-sm`.
- `AccountFilter.vue`, `TypeSelector.vue`: shared `.input .select` geometry and `aria-label`s. `ImportFileSelector.vue`: associated label, plain-language copy (removed "Click Me" / "Go ahead, do it"), inline success/error status instead of `alert()`, busy state, non-submitting button. `InternalTransferScanner.vue`: themed muted text (no `text-gray-500`), error state instead of silently reporting "No internal transfers", wrapping layout. `RecurringTransactionSection.vue`: labelled fields on the shared `.input`, themed buttons/colors, `type="button"`, scrollable rules table.
- Tests: `UpdateTransactionsTable.spec.js` (+6: aria-sort/sort buttons, column chooser, header/body alignment, scroll region, truncation titles, edit labels), `Transactions.spec.js` (+2), new `ImportFileSelector.spec.js` and `InternalTransferScanner.spec.js`. Full vitest 67 files / 437 tests, lint 0 errors, build OK.
- Not run: `transactions.cy.js` and the 320px browser pass (import/filter/long merchant/far-right edit, zoom); keyboard sorting is covered by button semantics in unit tests only.

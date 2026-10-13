# TP-20261007-004: Transactions Action Workbench

**Packet ID:** TP-20261007-004  
**Status:** Complete  
**Created:** 2026-10-07  
**Last updated:** 2026-10-13  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/completed/TP-20261007-004-transactions-action-workbench.md`  
**Workstream size:** One implementation packet  
**Depends on:** TP-20261007-002  
**Priority:** High  
**Series:** UI/UX reauthor, packet 3 of 8  

## Objective

Make Transactions feel like a focused transaction workbench: the data table is primary, everyday search/filter/review actions are immediately available, and advanced utilities such as import, recurring management, and transfer scanning are progressively disclosed.

## Confirmed current-state problems

File: `frontend/src/views/Transactions.vue`

Before the user reaches the table, the Activity surface can render:

1. PageHeader
2. a full Internal Transfer Scanner card
3. a full Import & Quick Search card
4. a full Filters card
5. a six-metric Filter Summary card
6. the Recent Transactions card

The scanner is also available as its own `Scanner` tab, so the same advanced tool is duplicated.

This forces a high volume of controls and explanatory copy ahead of the primary user object: transactions.

## Target hierarchy

1. Page identity + primary actions.
2. One compact transaction toolbar.
3. Active filters/result summary.
4. Transaction table.
5. Pagination.
6. Secondary workflows: Recurring, Scanner, Import/advanced actions.

## Required changes

### 1. Remove duplicate scanner surface

File: `frontend/src/views/Transactions.vue`

Remove the page-top Internal Transfer Scanner card and `showScanner` / `toggleScanner` path if it becomes unused. Keep the dedicated `Scanner` tab as the single scanner surface.

### 2. Consolidate Activity controls into one toolbar

Files:

- `frontend/src/views/Transactions.vue`
- shared base controls already used by this view

Replace separate "Top Controls" and "Filter Controls" cards with one compact Activity toolbar containing:

- search;
- date range;
- account;
- transaction type;
- export;
- a compact Import affordance or expandable import region.

Use labels/placeholders that remain understandable without paragraph-length helper copy.

Controls should wrap deliberately by group, not each inside its own mini-card.

### 3. Replace six-tile filter summary with an inline result summary

When filters are active, show a compact summary near the table header, for example:

- result count;
- filtered total amount;
- active filter chips;
- Clear filters.

Do not render six equal metric cards for categories, merchants, accounts, institutions unless one of those metrics directly drives an action.

Retain underlying computed data if other code relies on it, but do not let it dominate the UI.

### 4. Make the table the dominant Activity surface

Files:

- `frontend/src/views/Transactions.vue`
- `frontend/src/components/tables/UpdateTransactionsTable.vue`
- `frontend/src/components/tables/PaginationControls.vue` only as needed

Requirements:

- "Recent Transactions" / result count sits directly above table;
- export is adjacent to table actions;
- row density remains readable;
- edit/review actions are obvious without permanently showing every possible row control;
- loading/error/empty states occupy the table region rather than creating separate visual islands.

### 5. Progressive disclosure on mobile

On narrow screens:

- keep search + result count visible;
- move secondary filters into a single "Filters" disclosure/drawer/panel;
- show active-filter count on the trigger;
- no horizontal page overflow;
- table may use its existing responsive behavior, but filters must not form a vertical wall above it.

Do not add a new dependency solely for a drawer. An in-page disclosure is acceptable.

### 6. Clarify tab purpose

Keep:

- Activity
- Recurring
- Scanner

Activity is default. Scanner and Recurring should no longer duplicate major content above the tabs.

## Tests

Update:

- `frontend/src/views/__tests__/Transactions.spec.js`
- `frontend/src/views/__tests__/Transactions.cy.js`
- `frontend/cypress/e2e/transactions.cy.js` where relevant

Assert:

- scanner exists only in Scanner tab;
- table is present on default Activity path without opening secondary tools;
- filters still reach existing filter payload;
- active filter summary/clear works;
- CSV export behavior remains;
- pagination remains;
- mobile disclosure is keyboard accessible.

## Non-goals

- Do not change transaction API semantics.
- Do not alter recurring detection logic.
- Do not rewrite InternalTransferScanner internals.
- Do not change sign conventions or categorization behavior.

## Acceptance criteria

- [ ] Scanner duplication is removed.
- [ ] One compact Activity toolbar replaces multiple control cards.
- [ ] Transaction table is the primary visual surface.
- [ ] Filter summary is compact and actionable.
- [ ] Import is available without occupying permanent large vertical space.
- [ ] Recurring and Scanner stay available as secondary tabs.
- [ ] Mobile filters collapse cleanly.
- [ ] Existing filtering/export/pagination behavior is preserved.
- [ ] Focused Transactions tests pass.

## Validation

```bash
cd frontend
npm run test -- --run src/views/__tests__/Transactions.spec.js
npm run lint
npm run build
```

## Completion report

Report removed duplicate surfaces, new toolbar structure, mobile filter behavior, preserved workflows, tests, and deviations.

---

## Completion report (2026-10-13)

- **Finding that changed the diagnosis:** `TabbedPageLayout` renders only the `header`, active-tab and `sidebar` slots, never the default slot. The scanner/controls/filter/summary/duplicate-table cards in `Transactions.vue` sat in the default slot, so in the real app they were not rendered at all (only the unit test's stub rendered them). The Activity tab therefore had no search or filters. Moving the toolbar into `#Activity` restores them.
- **Removed:** the page-top Internal Transfer Scanner card plus `showScanner`/`toggleScanner`/`showControls`; the duplicated default-slot table card; the six-tile filter summary; Top Controls and Filter Controls cards. Scanner now exists only in the Scanner tab.
- **New Activity structure:** one `#activity-toolbar` (search, Filters toggle with active count, Import toggle revealing `ImportFileSelector`) → collapsible filters (date range, account, type; always visible at md+, disclosure below md via `aria-expanded`/`aria-controls`) → table card with "Transactions · N shown", Export CSV, inline summary (total, active-filter chips, Clear filters) → pagination.
- **Preserved:** filter payload/query-param sync, CSV export logic, pagination, row editing, Recurring tab. `filterSummary` unique-count computed retained but unrendered.
- **Tests:** `Transactions.spec.js` rewritten for summary, clear, scanner-once, toggles; `cypress/e2e/transactions.cy.js` scanner test replaced with a Scanner-tab check (not run, needs dev server). Vitest 49 files / 210 tests pass; lint 0 errors; build OK. Not viewed in a browser.
- **Deviations:** `Transactions.cy.js` component test not modified/run. Export button label unchanged.

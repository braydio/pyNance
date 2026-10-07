# TP-20261007-008: Investments Portfolio Hierarchy

**Packet ID:** TP-20261007-008  
**Status:** Ready  
**Created:** 2026-10-07  
**Last updated:** 2026-10-07  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/active/TP-20261007-008-investments-portfolio-hierarchy.md`  
**Workstream size:** One implementation packet  
**Depends on:** TP-20261007-002  
**Priority:** Normal  
**Series:** UI/UX reauthor, packet 7 of 8  

## Objective

Recompose Investments so portfolio value, allocation/performance, and holdings are immediately understandable while account linking, refresh operations, filters, and transaction detail remain secondary workflows.

## Confirmed current state

File: `frontend/src/views/Investments.vue`

The view is approximately 900 lines and renders four long sections with its own scroll navigation:

- Portfolio Overview
- Holdings
- Performance
- Recent Investment Transactions

Portfolio Overview includes account linking and refresh controls before the user reaches the core portfolio data. Holdings and transactions each carry their own filter surfaces. Much of the visual and interaction logic is inline in one file.

## Target hierarchy

1. portfolio state: total value + meaningful change/performance when available;
2. account/connection attention if needed;
3. holdings/allocation;
4. performance;
5. recent investment activity;
6. maintenance/link/refresh actions.

## Required changes

### 1. Reauthor Portfolio Overview

File: `frontend/src/views/Investments.vue`

The first visible portfolio surface should prioritize data already available in the view:

- total holdings value;
- account count;
- institution/account grouping;
- performance/change only when backed by current data.

Move "Link New Investments Account" and refresh/sync controls into a secondary action region. Do not let onboarding/maintenance precede an existing portfolio's value.

### 2. Simplify section navigation

Keep in-page navigation only if it materially helps the long page. Use short labels and a restrained active state.

If the reauthored page becomes sufficiently shorter, replace the large section-nav card with a compact sticky/subnav or remove it.

### 3. Make holdings the primary detail surface

Use account-level summary rows as currently computed, with expandable holdings underneath. Improve scan priority:

- account/institution;
- total value;
- holdings count;
- then security-level detail.

Filters should be compact and directly attached to Holdings, not visually equal to the holdings data.

### 4. Keep performance interpretive

Performance should answer the trend question without forcing users through maintenance controls. Use the shared surface hierarchy from TP-20261007-002.

Do not fabricate returns if the current data contract does not provide them.

### 5. Demote investment transactions

Recent Investment Transactions remains available after Holdings/Performance. Compact its filters using the same disclosure principles as Transactions packet 004.

### 6. Decompose view where it reduces cognitive/code load

The current 894-line single file may be split into focused components under `frontend/src/components/investments/`, for example:

- portfolio summary;
- holdings section;
- activity section;
- maintenance actions.

Only split where it creates clear ownership. Do not create thin wrapper components solely to reduce line count.

### 7. Mobile behavior

- no wide filter wall before content;
- account holding summaries remain scannable;
- expanded security detail does not force page-level horizontal scrolling;
- section navigation does not consume a full screen.

## Tests

Update:

- `frontend/src/views/__tests__/Investments.spec.js`

Add focused component tests if decomposition introduces meaningful new components.

Cover:

- portfolio summary precedes linking/maintenance;
- holdings expansion still works;
- current filters still drive requests;
- transaction pagination remains;
- refresh/link actions remain reachable;
- section navigation behavior if retained.

## Non-goals

- Do not alter holdings valuation logic.
- Do not calculate unsupported performance metrics.
- Do not change investment API contracts.
- Do not change Plaid investment refresh semantics.

## Acceptance criteria

- [ ] Existing portfolio value/data appears before account-link maintenance.
- [ ] Holdings are the primary detail surface.
- [ ] Filters are visually secondary and contextual.
- [ ] Investment activity is lower priority than holdings/performance.
- [ ] Page-level visual hierarchy uses shared foundation tokens.
- [ ] Mobile does not present a filter/control wall.
- [ ] Existing investment data behavior is preserved.
- [ ] Focused Investments tests pass.

## Validation

```bash
cd frontend
npm run test -- --run src/views/__tests__/Investments.spec.js
npm run lint
npm run build
```

## Completion report

Report new section order, any component extraction, maintenance-action placement, responsive behavior, tests, and deviations.

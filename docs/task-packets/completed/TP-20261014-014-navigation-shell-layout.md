# TP-20261014-014: Navbar, Responsive Tabs and Shared Spacing

**Packet ID:** TP-20261014-014  
**Status:** Complete  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** docs/task-packets/completed/TP-20261014-014-navigation-shell-layout.md  
**Depends on:** TP-20261014-010, TP-20261014-011  
**Priority:** High  
**Workstream size:** One focused UI packet  
**Source audit:** docs/frontend/UI_FIELD_AUDIT_2026-10-14.md

## Exact file paths
- frontend/src/components/layout/Navbar.vue
- frontend/src/components/layout/AppLayout.vue
- frontend/src/components/layout/BasePageLayout.vue
- frontend/src/components/layout/TabbedPageLayout.vue
- frontend/src/components/ui/PageHeader.vue
- frontend/src/components/ui/ChartWidgetTopBar.vue
- frontend/src/views/Institutions.vue

## Confirmed current state
Navbar <=760px hides horizontally scrollable nav scrollbar without visual cue; app uses outer max-w-7xl gutters and BasePageLayout py-6/gap-6; TabbedPageLayout wraps tabs and reserves fixed sidebar width. Institutions.vue nests a BasePageLayout in another.

## Required implementation
Give mobile nav an overflow fade, accessible More, or scroll cue and keep active tab visible/focusable. One outer gutter owner, section rhythm 16/24/32px with flex min-width:0; prevent double padding. Tabs on narrow screens use one scrollable row with visible affordance and aria keyboard navigation; sidebar stacks below main content <=1023px, no overlapping CTA. ChartWidgetTopBar and PageHeader control/title wrap independently; no fixed min-width summary pushing controls outside. Remove Institutions nested page wrapper with corresponding visual test.

## Validation
Navbar.spec.js, AppLayout.spec.ts, BasePageLayout.spec.ts, TabbedPageLayout.spec.ts; 320/390/768/1024/1440 both themes, zoom 200%, keyboard nav; no document horizontal overflow.

## Non-goals
No new route labels or global redesign.

## Completion contract
Check AGENTS.md and docs/task-packets/README.md, TRACKER and INDEX; validate named paths only. Mark In Progress, implement ordered fixes, run focused tests and lint/build. After completion move packet to completed/, update INDEX/TRACKER atomically, commit to origin/main without force. Report files, browser validation vs static assumptions, exact commands/output and deviations. Coordinate overlapping files with prerequisite packets; no broad refactor.

## Completion report

- `Navbar.vue`: on <=760px the link row is a single scrollable row with edge fades that appear only on the side with hidden links (updated on scroll/resize), snap alignment, and the current destination is scrolled into view on mount, route change and click; secondary labels raised to 0.875rem. Link routes/labels unchanged.
- `AppLayout.vue` remains the only owner of the horizontal gutter (`max-w-7xl px-4 sm:px-6 lg:px-8`), now with `min-w-0` on `main` and the gutter; `BasePageLayout.vue` keeps `py-6`/`gap-6` defaults (16/24/32px rhythm via `gap-4|6|8`), gains `min-w-0` and documents "one layout per view".
- `TabbedPageLayout.vue`: <=768px tabs become one non-wrapping scrollable row with edge fades, snap alignment and the active tab scrolled into view; existing ARIA tablist, roving tabindex and arrow/Home/End navigation kept; sidebar stacks below content under `lg` (`max-lg:w-full`) with `min-w-0`, and the blanket `z-10` was removed so it cannot overlay content.
- `ChartWidgetTopBar.vue`: controls wrap (`flex-wrap min-w-0 max-w-full`, no `flex-shrink-0`); the summary no longer has a fixed `min-w-[150px]`/`nowrap` below 640px. `PageHeader.vue` actions get `min-width: 0`/`max-width: 100%`.
- `Institutions.vue`: the two sibling `BasePageLayout` wrappers (double vertical padding) are one.
- Tests: extended `Navbar.spec.js`, `TabbedPageLayout.spec.ts`, `BasePageLayout.spec.ts`, `AppLayout.spec.ts`; new `ChartWidgetTopBar.spec.js` and `views/__tests__/Institutions.spec.js`. Full vitest, lint (0 errors) and build pass.
- Not run: 320/390/768/1024/1440 browser passes, 200% zoom and document-overflow measurement (jsdom has no layout, so scroll affordances are tested through mocked scroll metrics).

# TP-20261014-014: Navbar, Responsive Tabs and Shared Spacing

**Packet ID:** TP-20261014-014  
**Status:** Ready  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** docs/task-packets/active/TP-20261014-014-navigation-shell-layout.md  
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

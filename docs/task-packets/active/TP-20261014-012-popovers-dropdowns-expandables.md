# TP-20261014-012: Dropdowns, Popovers and Expandable State

**Packet ID:** TP-20261014-012  
**Status:** Ready  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** docs/task-packets/active/TP-20261014-012-popovers-dropdowns-expandables.md  
**Depends on:** TP-20261014-010, TP-20261014-011  
**Priority:** High  
**Workstream size:** One focused UI packet  
**Source audit:** docs/frontend/UI_FIELD_AUDIT_2026-10-14.md

## Exact file paths
- frontend/src/components/ui/GroupedCategoryDropdown.vue
- frontend/src/components/ui/FuzzyDropdown.vue
- frontend/src/components/ui/TogglePanel.vue
- frontend/src/components/charts/ChartDetailsSidebar.vue
- frontend/src/components/dashboard/CategoryBreakdownSection.vue
- frontend/src/components/widgets/TopAccountSnapshot.vue

## Confirmed current state
GroupedCategoryDropdown is clickable div tabindex=0 but only Escape handler; absolute z-40 popover lacks bounded height. CategoryBreakdownSection BasePanel has overflow-hidden, likely clipping absolute dropdown. FuzzyDropdown waits 180ms on blur and uses z-10, hardcoded gray empty state. TogglePanel uses Tailwind .dark and --color-bg-primary fallback white despite app theme data-theme.

## Required implementation
Convert grouped trigger to button aria-expanded/controls, selected count, Enter/Space/Escape focus return; independent group expand and selection controls. Menu max-height:min(20rem,50dvh), internal overflow-y:auto and viewport-safe alignment. Remove BasePanel ancestor overflow-hidden; clip only chart canvas region. FuzzyDropdown robust click-away and focus-within (no blur timer), label search and max selection feedback. TogglePanel semantic surfaces, aria-expanded and reduced-motion; preserve v-model. Check ChartDetailsSidebar and TopAccountSnapshot edit-menu stacking, no blanket huge z-index.

## Validation
New frontend/src/components/ui/__tests__/DisclosureControls.spec.js; ChartDetailsSidebar.spec.js, DashboardSections.spec.ts; Cypress 320px category menu open at viewport edge, keyboard group operations, light/dark/zoom. lint/build.

## Non-goals
No category selection or group persistence semantic changes.

## Completion contract
Check AGENTS.md and docs/task-packets/README.md, TRACKER and INDEX; validate named paths only. Mark In Progress, implement ordered fixes, run focused tests and lint/build. After completion move packet to completed/, update INDEX/TRACKER atomically, commit to origin/main without force. Report files, browser validation vs static assumptions, exact commands/output and deviations. Coordinate overlapping files with prerequisite packets; no broad refactor.

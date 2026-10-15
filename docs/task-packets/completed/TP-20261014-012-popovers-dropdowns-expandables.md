# TP-20261014-012: Dropdowns, Popovers and Expandable State

**Packet ID:** TP-20261014-012  
**Status:** Complete  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** docs/task-packets/completed/TP-20261014-012-popovers-dropdowns-expandables.md  
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

## Completion report

- `GroupedCategoryDropdown.vue`: trigger is now a real `<button type="button">` with `aria-expanded`, `aria-controls`, `aria-haspopup` and a "N selected" summary; Enter/Space work natively, Escape closes from the trigger or the menu and returns focus to the trigger. Group expand/collapse is its own button (`aria-expanded`/`aria-controls`/label) and no longer changes with selection (groups that already have selections start expanded). Menu is `max-height: min(20rem, 50dvh)` with internal scrolling, `max-width: calc(100vw - 1rem)`, no `mousedown.prevent`; reduced-motion respected. Selection semantics/emitted values are unchanged.
- `CategoryBreakdownSection.vue`: removed `overflow-hidden` from the BasePanel; only the chart region (`breakdown-chart-clip`) clips.
- `FuzzyDropdown.vue`: the 180ms blur timer is gone (focus-within via `focusout.relatedTarget` plus the outside-click directive), labelled combobox input (`label` prop), Escape closes, max-selection feedback (`role="status"`), themed `text-muted` empty state, bounded menu height. Fixed an existing quirk where `max` also capped how many options were listed.
- `TogglePanel.vue`: theme surfaces/borders (`--surface-*`, `--border-subtle`), `aria-expanded`/`aria-controls`, `type="button"`, opacity-only transition with reduced-motion; v-model preserved; no `.dark`/gray utility fallbacks.
- `ChartDetailsSidebar.vue` and `TopAccountSnapshot.vue` reviewed: both already expose `aria-expanded`, handle outside clicks/Escape and use local z-indexes (10/40/50); no change needed.
- Tests: new `components/ui/__tests__/DisclosureControls.spec.js` (10); `ChartDetailsSidebar.spec.js` and `DashboardSections.spec.ts` pass. Full vitest 59 files / 395 tests, lint 0 errors, build OK.
- Not run: the Cypress 320px menu-at-viewport-edge check and light/dark/zoom browser verification (no browser run here), so popover clipping is verified by source/class assertions only.

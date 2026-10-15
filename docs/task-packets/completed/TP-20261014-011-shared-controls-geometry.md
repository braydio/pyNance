# TP-20261014-011: Shared Fields, Buttons, Date and Select Geometry

**Packet ID:** TP-20261014-011  
**Status:** Complete  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** docs/task-packets/completed/TP-20261014-011-shared-controls-geometry.md  
**Depends on:** TP-20261014-010  
**Priority:** High  
**Workstream size:** One focused UI packet  
**Source audit:** docs/frontend/UI_FIELD_AUDIT_2026-10-14.md

## Exact file paths
- frontend/src/assets/css/main.css
- frontend/src/components/base/BaseInput.vue
- frontend/src/components/base/BaseSelect.vue
- frontend/src/components/base/BaseButton.vue
- frontend/src/components/ui/Button.vue
- frontend/src/components/DateRangeSelector.vue

## Confirmed current state
.input uses px-2 py-1 while ui-control-input px-3 py-1.5; BaseInput/BaseSelect sm/md spacing differs; native fields and buttons use different heights and focus rings across routes.

## Required implementation
Define --control-height 2.5rem, --control-height-sm 2.25rem, padding/radius/focus/disabled tokens in main.css. Harmonize .input, .select, .btn, UiButton, BaseInput/BaseSelect/BaseButton; keep compatible prop/v-model/emit semantics and explicit submit. Non-submit actions type=button. Do not force button/input sizing on checkbox/radio, textarea or tiny chart chips. Native date and select arrows and selected option legible in both themes, min-width:0/max-width:100%. DateRangeSelector uses visible From/Through labels, matching controls and responsive wrapping at 320px. Associate invalid errors via aria and prevent zoom cropping.

## Validation
New frontend/src/components/base/__tests__/ControlGeometry.spec.js; BillForm.spec.ts submit/regression. 320/390/768/1280 widths, 200% text zoom, both themes. npm run test -- --run src/components/base/__tests__/ControlGeometry.spec.js && npm run lint && npm run build.

## Non-goals
No business validation or API changes.

## Completion contract
Check AGENTS.md and docs/task-packets/README.md, TRACKER and INDEX; validate named paths only. Mark In Progress, implement ordered fixes, run focused tests and lint/build. After completion move packet to completed/, update INDEX/TRACKER atomically, commit to origin/main without force. Report files, browser validation vs static assumptions, exact commands/output and deviations. Coordinate overlapping files with prerequisite packets; no broad refactor.

## Completion report

- `assets/css/main.css`: control tokens (`--control-height` 2.5rem, `--control-height-sm` 2.25rem, padding, radius, focus ring, disabled opacity); `.input`/new `.select` share height/padding/radius/min-width:0/max-width:100%, `aria-invalid` and `.field-error` styling; `.btn` (previously undefined, so UiButton `btn-outline`/`btn-sm`/`btn-pill` had no base styles) now has base, hover, focus, disabled, `.btn-outline`, `.btn-sm`, `.btn-pill`, placed before `.btn-primary/-success/-alert` so variants keep their colors; `color-scheme: dark|light` per theme so native date picker/select arrows and option lists are legible; `select option` uses theme surface/text.
- `BaseInput`/`BaseSelect`/`BaseButton`: same min-heights per size, `text-sm` (no `text-xs`), `min-w-0 max-w-full`, accessible `--control-border`; `BaseInput`/`BaseSelect` gain `invalid` + `describedby` props wired to `aria-invalid`/`aria-describedby`. v-model, `enter`, `change`, `click` semantics unchanged. `UiButton` gains a `type` prop defaulting to `button` (explicit `submit` still works; BillForm already sets it).
- `DateRangeSelector`: visible From/Through labels, fields use the shared `.input` class, wraps (`flex-wrap`, `flex: 1 1 9rem`, `min-width: 0`) so it can shrink at 320px.
- Tests: new `components/base/__tests__/ControlGeometry.spec.js` (tokens, shared height/padding/radius, native color-scheme, variant order, aria association, UiButton type, DateRangeSelector); `BasePrimitives.spec.ts` and `BillForm.spec.ts` still pass. Full vitest 58 files / 385 tests, lint 0 errors, build OK.
- Not done: no browser check at 320/390/768/1280 or 200% zoom (static class/token checks only); native checkbox/radio, textarea and tiny chart chips were deliberately not resized.

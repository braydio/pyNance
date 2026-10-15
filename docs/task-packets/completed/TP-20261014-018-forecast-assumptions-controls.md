# TP-20261014-018: Forecast Scenarios and Assumptions UI Density

**Packet ID:** TP-20261014-018  
**Status:** Complete  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** docs/task-packets/completed/TP-20261014-018-forecast-assumptions-controls.md  
**Depends on:** TP-20261014-010, TP-20261014-011, TP-20261014-012, TP-20261014-013  
**Priority:** High  
**Workstream size:** One focused UI packet  
**Source audit:** docs/frontend/UI_FIELD_AUDIT_2026-10-14.md

## Exact file paths
- frontend/src/views/Forecast.vue
- frontend/src/components/forecast/ForecastLayout.vue
- frontend/src/components/forecast/ForecastSummaryPanel.vue
- frontend/src/components/forecast/ForecastChart.vue
- frontend/src/components/forecast/ForecastScenarioComparison.vue
- frontend/src/components/forecast/ForecastAdjustmentsForm.vue
- frontend/src/components/forecast/ForecastBreakdown.vue

## Confirmed current state
ForecastLayout root class p-6 bg-gray-50 conflicts with Nightfox; error/loading text-gray-500/text-red-600 fixed. Dense nested assumptions/advanced details and source event lists; chart aspect/model/window/simulation/scenario controls vary in size.

## Required implementation
Remove bg-gray-50 and hardcoded foregrounds; use theme surface + responsive padding without two outer gutters. Forecast summary/chart/scenario results first, assumptions as readable collapsed disclosure, Advanced model controls last. Align label/select/checkbox/number inputs, label rate units and applied vs draft, compare scenario table in local horizontal scroll. Limit nested surface levels to two, long source references wrap; source modal uses packet 013 focus/scroll. Preserve data/model requests and settings.

## Validation
ForecastLayout.spec.ts, ForecastChart.spec.ts, ForecastSummaryPanel.spec.ts, ForecastV2.spec.ts, frontend/cypress/e2e/forecast-v2.cy.js. All disclosures open, 320/1280 and both themes, long amount/source text; lint/build.

## Non-goals
No forecast engine or calculation changes.

## Completion contract
Check AGENTS.md and docs/task-packets/README.md, TRACKER and INDEX; validate named paths only. Mark In Progress, implement ordered fixes, run focused tests and lint/build. After completion move packet to completed/, update INDEX/TRACKER atomically, commit to origin/main without force. Report files, browser validation vs static assumptions, exact commands/output and deviations. Coordinate overlapping files with prerequisite packets; no broad refactor.

## Completion report

- `ForecastLayout.vue`: removed `p-6 bg-gray-50` (the page layout owns the single gutter, theme background shows through) and the hardcoded `text-gray-500`/`text-red-600` status text (now `text-muted`/`text-negative` with `role="status"`/`role="alert"`). Order kept as results first (summary, chart, scenarios, breakdown), assumptions as a closed `<details>`, Advanced model controls last. Label/select/checkbox controls share a `.control-field`/`.control-check` pattern with the shared select geometry; inner "cards" inside the assumptions disclosure were flattened so there are at most two surface levels; long source references/labels wrap; hardcoded greens/blues/light surfaces replaced with theme tokens (`--text-positive`, `--text-link`, `--surface-2`, accent mixes).
- `ForecastSummaryPanel.vue`: manual inputs are labelled "($ per day)" with an explicit note that both values are dollars per day (not percentages) and apply as you type, wired through `aria-describedby`; hardcoded error/accent colors replaced with theme tokens. `ForecastScenarioComparison.vue` already scrolled its table in a local, focusable region; its delta colors now use the contrast-verified text roles. `ForecastAdjustmentsForm.vue`: every field has an accessible name (`aria-label`) and shared select geometry; submit/reset behavior unchanged. Small text in all forecast components raised to >= 0.8125rem.
- Source-details modal: focus/scroll behavior comes from TP-013 (`useModalA11y`). No data requests, model settings or calculations were touched.
- Tests: `ForecastLayout.spec.ts` (+4), `ForecastSummaryPanel.spec.ts` (+1), new `ForecastAdjustmentsForm.spec.ts`; `ForecastChart.spec.ts`, `ForecastV2.spec.ts` pass. Full vitest 71 files / 455 tests, lint 0 errors, build OK.
- Not run: `forecast-v2.cy.js` and the 320/1280 two-theme browser pass with all disclosures open; `ForecastChart.vue` was only touched for small-text sizing.

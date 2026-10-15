# TP-20261014-018: Forecast Scenarios and Assumptions UI Density

**Packet ID:** TP-20261014-018  
**Status:** Ready  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** docs/task-packets/active/TP-20261014-018-forecast-assumptions-controls.md  
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

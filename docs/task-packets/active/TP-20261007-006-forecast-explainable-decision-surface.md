# TP-20261007-006: Forecast Explainable Decision Surface

**Packet ID:** TP-20261007-006  
**Status:** Ready  
**Created:** 2026-10-07  
**Last updated:** 2026-10-07  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/active/TP-20261007-006-forecast-explainable-decision-surface.md`  
**Workstream size:** One implementation packet  
**Depends on:** TP-20261007-002  
**Priority:** Normal  
**Series:** UI/UX reauthor, packet 5 of 8  

## Objective

Make Forecast answer "where am I headed, what changes that outcome, and why should I trust it?" without forcing the user through model controls and source evidence before seeing the forecast.

## Confirmed current-state problems

Files:

- `frontend/src/views/Forecast.vue`
- `frontend/src/components/forecast/ForecastLayout.vue`
- `frontend/src/components/forecast/ForecastSummaryPanel.vue`
- `frontend/src/components/forecast/ForecastChart.vue`
- `frontend/src/components/forecast/ForecastBreakdown.vue`
- `frontend/src/components/forecast/ForecastAdjustmentsForm.vue`

Current issues:

1. Page subtitle is literally "With complex voodoo magic".
2. ForecastLayout shows summary/configuration, a four-control model row, manual/realized adjustment lists, and a large Auto-Detected Adjustments evidence card before the main ForecastChart.
3. Advanced concepts such as graph mode, moving average, normalization, confidence, source matching fields, and model provenance compete with the outcome.
4. Source evidence is valuable for trust but is presented as permanent primary content instead of on demand.

## Target hierarchy

1. **Outcome:** projected balance / net change / horizon and chart.
2. **Scope:** accounts/groups and timeframe that define the forecast.
3. **Drivers:** upcoming inflows/outflows and meaningful adjustments.
4. **Explain:** confidence/source evidence on demand.
5. **Tune:** advanced model controls under an Advanced disclosure.

## Required changes

### 1. Fix page copy

File: `frontend/src/views/Forecast.vue`

Replace "With complex voodoo magic" with concise outcome language explaining that the page projects balances from known cash flows and adjustments.

### 2. Move chart/outcome above model tuning

File: `frontend/src/components/forecast/ForecastLayout.vue`

After loading/error handling, render:

- ForecastSummaryPanel in a compact outcome form;
- ForecastChart;
- primary forecast breakdown/drivers.

Move the current general control row and evidence-heavy adjustment sections below the chart or into disclosures.

### 3. Simplify ForecastSummaryPanel

File: `frontend/src/components/forecast/ForecastSummaryPanel.vue`

Prioritize:

- projected/net balance;
- projected change over selected horizon;
- included account scope;
- major warning if data is insufficient.

Manual income/liability rate and detailed scope tuning should not appear as equal-weight hero metrics unless directly needed.

### 4. Create Basic vs Advanced controls

In `ForecastLayout.vue`:

Basic, visible:
- account/group scope;
- forecast horizon/view type;
- chart aspect only if it materially changes the question.

Advanced, collapsed by default:
- graph mode;
- moving average window;
- normalize history;
- manual rate/model tuning.

Use native accessible disclosure or existing primitives. No new UI dependency.

### 5. Collapse evidence-heavy adjustment detail

Auto-detected wages/rent and source transactions remain available, but default presentation should be a concise "Forecast assumptions" summary:

- number/value of active assumptions;
- manual vs auto-detected;
- clear Review assumptions action.

Source transactions and matching fields open only when the user requests them.

### 6. Keep interpretability

Do not hide provenance permanently. Every auto-detected adjustment must still expose:

- reason;
- confidence when available;
- source transaction details;
- matching fields where currently present.

The change is information priority, not information deletion.

### 7. Empty/error states explain the next action

"No forecast data" should suggest the smallest relevant next step, such as selecting an account or adding/confirming an adjustment, based on currently available state.

## Tests

Update:

- `frontend/src/components/forecast/__tests__/ForecastLayout.spec.ts`
- `frontend/src/components/forecast/__tests__/ForecastSummaryPanel.spec.ts`
- `frontend/src/components/forecast/__tests__/ForecastChart.spec.ts`

Cover:

- chart/outcome precedes advanced controls;
- advanced controls collapsed by default;
- assumptions details can be opened;
- existing control values still feed `useForecastData`;
- source evidence remains reachable;
- new copy removes placeholder/joke language.

## Non-goals

- Do not modify forecast engine math/API.
- Do not remove model controls.
- Do not remove provenance.
- Do not add a new forecasting model.

## Acceptance criteria

- [ ] Forecast outcome/chart appears before model tuning and evidence detail.
- [ ] Page copy is plain-language and credible.
- [ ] Basic controls are small and obvious.
- [ ] Advanced controls are collapsed by default.
- [ ] Auto/manual assumptions have a concise summary.
- [ ] Provenance/source transactions remain reachable.
- [ ] Existing forecast parameters still reach the same data contract.
- [ ] Focused Forecast tests pass.

## Validation

```bash
cd frontend
npm run test -- --run src/components/forecast/__tests__/ForecastLayout.spec.ts src/components/forecast/__tests__/ForecastSummaryPanel.spec.ts src/components/forecast/__tests__/ForecastChart.spec.ts
npm run lint
npm run build
```

## Completion report

Report reordered sections, Basic/Advanced split, assumptions disclosure, preserved controls/provenance, tests, and deviations.

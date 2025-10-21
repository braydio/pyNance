# Planning View Layout & Interaction Guide

The Planning route (`frontend/src/views/Planning.vue`) composes bill management and allocation tooling around the planning state singleton exposed by `usePlanning`. This document captures the layout conventions, key component responsibilities, and the data flows that connect the UI to the planning APIs so frontend and backend contributors can coordinate changes.

## Page Layout

- **Page shell** – `BasePageLayout` wraps the entire view to provide consistent spacing. `PageHeader` supplies the "Planning" title, calendar icon, and a primary "Create bill" action that seeds the bill form for new entries.
- **Responsive grid** – The body is a two-column grid (`xl:grid-cols-[2fr,1fr]`).
  - **Left column** – Contains a bill management stack:
    - `BillList` housed inside a padded `Card` for browsing existing bills.
    - A second `Card` with the active form state (`BillForm`) and a dynamic heading (`Create bill` or `Edit bill`). A `Reset` action returns the form to its persisted state when editing.
  - **Right column** – Focused on scenario insights:
    - `PlanningSummary` renders bill totals, allocation summaries, and exposes a refresh hook.
    - An `Allocator` component wrapped in a `Card` manages percent-based allocation targets for the active scenario.

## Primary Components

### BillList

- **Inputs** – Receives the filtered `billsForScenario`, the active currency code, and the `selectedBillId` for row highlighting.
- **Slot actions** – The `actions` slot hosts the inline "Add bill" shortcut.
- **Events** – Emits `select`, `edit`, and `delete` events that bubble to the view handlers for selection, form population, and deletion.

### BillForm

- **Mode awareness** – `mode` toggles between `'create'` and `'edit'`, driven by the internal `editingBill` ref.
- **Draft propagation** – Emits `update:bill` so the view can stash draft state per scenario before persistence.
- **Persistence hooks** – `save` is routed through `handleSaveBill`, which delegates to `persistBill` and reconciles optimistic updates; `cancel` hides the form without mutating existing data.

### PlanningSummary

- **Scenario scope** – Receives the resolved `scenarioId` and `currencyCode` from the active scenario computed.
- **Refresh contract** – Emits `refresh` when downstream panels need a data refresh. The view maps this to `ensureScenario()` so remote updates stay in sync.

### Allocator

- **Two-way binding** – Uses `v-model="allocationModel"` to keep the UI slider/grid in sync with scenario allocations. The model is prefilled from `allocationsToPercentMap` when the active scenario changes.
- **Change events** – Emits `change` with `{ allocations }`, which the view maps through `mergePercentAllocations` before handing off to `persistScenarioAllocations` for optimistic persistence.

## Composables & State Orchestration

- `usePlanning()` exposes a read-only `state` object with bills, scenarios, and mode flags. The view relies on it for:
  - Resolving the active account via the `accountId` query parameter.
  - Computing `activeScenario`, `currencyCode`, `billsForScenario`, and derived allocation categories (existing scenario targets + default fallbacks like `savings:emergency`).
- Helper exports imported from `usePlanning`:
  - `ensureScenarioForAccount` guarantees a scenario exists for the selected account and tracks it in `activeScenarioIdByAccount`.
  - `persistBill`, `removeBill`, and `persistScenarioAllocations` wrap local-vs-API persistence modes with optimistic updates and rollback safety.
- Reactive guards:
  - Watchers hydrate `allocationModel` whenever `activeScenario.allocations` change and clear stale selections if a bill disappears.
  - On mount and when `accountId` changes, the view calls `ensureScenario()` to guarantee planning context is ready before rendering child components.

## Key Interactions

- **Start creating** – `startCreating()` clears selection, resets drafts, shows the form, and keeps the component in `'create'` mode.
- **Edit selection** – `handleSelectBill`/`handleEditBill` clone the chosen bill into `editingBill`, set `selectedBillId`, and reveal the form with existing values.
- **Persist bill** – `handleSaveBill` merges the payload with active scenario/account identifiers, delegates to `persistBill`, and updates selection based on whether it was a create or update flow. Errors are surfaced to the console for future toast integration.
- **Draft management** – `handleDraftUpdate` preserves scenario metadata on drafts so subsequent saves include the correct `accountId`/`scenarioId` in API mode.
- **Deletion** – `handleDeleteBill` confirms intent, calls `removeBill`, and clears UI state if the deleted bill was active.
- **Form reset** – `resetForm` reloads persisted data when editing or clears drafts in create mode.
- **Allocation updates** – `handleAllocationChange` merges incoming percentages with existing allocations, generates IDs as needed, and persists via `persistScenarioAllocations`.
- **Summary refresh** – `refreshSummary` re-invokes `ensureScenario()` so downstream components pull the latest planning snapshot after external changes.

## Backend Planning API Dependencies

When `usePlanning` is in API mode, the view depends on `frontend/src/services/planningService.ts` to reach the Flask planning endpoints:

- **Bills** – `persistBill` maps to `POST /planning/bills` for creates, `PUT /planning/bills/:id` for updates, and `removeBill` calls `DELETE /planning/bills/:id`.
- **Allocations** – `persistScenarioAllocations` issues `PUT /planning/scenarios/:scenarioId/allocations` with the merged allocation list.

Backend changes to these contracts (shape, validation, or endpoint paths) must be coordinated with the Planning view and `usePlanning` composable to avoid breaking optimistic flows and local fallbacks. Keep the request/response schema aligned with the typings in `frontend/src/types/planning.ts` and update this document when API-side adjustments land.

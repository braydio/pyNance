# Planning UI Reference

_Last updated: 2025-02-20_

The Planning surface now ships a cohesive set of Vue components that compose the budgeting and allocation workflow. This guide captures the public interfaces—props, emits, and shared utilities—so backend and follow-on frontend work can rely on the documented contracts.

## Overview

```
Planning.vue
├── BillList.vue
├── BillForm.vue
├── Allocator.vue
└── PlanningSummary.vue
```

The view persists state through `usePlanning`, which stores a `PlanningState` record in local storage (version `4`). Components communicate exclusively through events; parent logic updates the global store via `updatePlanning` and selector helpers in `frontend/src/selectors/planning.ts`.

`PlanningState` includes a `mode` flag (`'local'` or `'api'`) that toggles between browser-only persistence and optimistic API orchestration. The composable hydrates from local storage, applies migrations, and exposes helpers to switch modes at runtime.

## Components

### `BillForm.vue`

| Prop | Type | Description |
| --- | --- | --- |
| `bill` | `Bill \| null` | Optional existing bill to edit. When `null` the form starts blank. |
| `currencyCode` | `string` | ISO currency code used for previews (default `USD`). |
| `mode` | `'create' \| 'edit'` | Controls submit labelling and reset behaviour (default `create`). |
| `visible` | `boolean` | Toggles the form/empty-state panel. |

**Emits**

- `update:bill` (`BillFormState`): fires on every input change so parents can retain a draft.
- `save` (`BillFormSubmitPayload`): emits a normalized payload with `amountCents`, `frequency`, and trimmed strings after validation.
- `cancel`: signals the parent to close or reset the form.

**Notes**

- Validation enforces required fields, positive currency values, and a valid ISO date.
- Amount parsing lives in `frontend/src/utils/planning.ts` to keep logic shared.

### `BillList.vue`

| Prop | Type | Description |
| --- | --- | --- |
| `bills` | `Bill[]` | Scenario-filtered bills to display. |
| `currencyCode` | `string` | Currency for amount formatting (default `USD`). |
| `selectedBillId` | `string \| null` | Highlights the active list item. |

**Emits**

- `select` (`Bill`): row clicked; the parent may open the form.
- `edit` (`Bill`): edit button pressed; always passes the full bill.
- `delete` (`string`): delete button pressed; payload is the bill ID.

The component uses native date formatting and the shared currency helper. Bills flagged with `origin: 'predicted'` render a badge.

### `Allocator.vue`

| Prop | Type | Description |
| --- | --- | --- |
| `categories` | `string[]` | Ordered allocation targets (e.g., `['savings:emergency']`). |
| `modelValue` | `Record<string, number>` | Percentages per category for `v-model`. |
| `currencyCode` | `string` | Currency for preview text (default `USD`). |
| `availableCents` | `number` | Scenario planning balance in cents (default `0`). |

**Emits**

- `update:modelValue` (`Record<string, number>`): updates the bound allocation map.
- `change` ({ `allocations`, `totalPercent`, `remainingPercent`, `totalCents`, `isValid` }): rich payload for parent validation and persistence.

Sliders clamp values so the total never exceeds 100%, leveraging `clampAllocations` and `sanitizePercent` from `frontend/src/utils/planning.ts`.

### `PlanningSummary.vue`

| Prop | Type | Description |
| --- | --- | --- |
| `scenarioId` | `string \| undefined` | Override the active scenario (defaults to `usePlanning().state`). |
| `currencyCode` | `string \| undefined` | Optional currency override; falls back to the scenario currency or `USD`. |

**Emits**

- `refresh`: hook for future integrations to recompute data or trigger refetches.

The summary displays totals derived from selectors: `selectTotalBillsCents`, `selectAllocatedCents`, and `selectRemainingCents`.

## View Composition (`Planning.vue`)

- Reads `accountId` from the route query, ensuring each account receives its own scenario. Missing scenarios are seeded with a zero-balance record (`currencyCode: 'USD'`).
- Filters bills by `scenarioId`, maintains selection state, and confirms deletions (simple `window.confirm` placeholder pending design-system dialogs).
- Persists allocation adjustments by mapping `Allocator` payloads back into `Scenario.allocations` via `mergePercentAllocations` and the `persistScenarioAllocations` helper.
- Delegates bill creation, updates, and deletions to `persistBill`/`removeBill`, allowing optimistic state reconciliation when `mode === 'api'`.

## Utilities

`frontend/src/utils/planning.ts` centralises shared logic:

- `billToFormState` / `normaliseBillForm`: convert between persisted bills and editable drafts.
- `clampAllocations`, `sanitizePercent`: enforce percentage bounds.
- `allocationsToPercentMap`, `mergePercentAllocations`: bridge array-based allocations with the allocator's record format.

The utilities are fully unit-tested (`frontend/src/utils/__tests__/planning.spec.ts`).

## Testing coverage

- `frontend/src/components/planning/__tests__/BillForm.spec.ts`
- `frontend/src/components/planning/__tests__/Allocator.spec.ts`
- `frontend/src/utils/__tests__/planning.spec.ts`
- `frontend/src/composables/__tests__/usePlanning.spec.ts`
- `frontend/src/views/__tests__/Planning.spec.js`
- `frontend/src/views/__tests__/Planning.cy.js` (selector-level assertions)

## Composable surface

`frontend/src/composables/usePlanning.ts` exposes additional runtime helpers alongside the read-only `state` and `updatePlanning` patcher:

- `ensureScenarioForAccount(accountId, { currencyCode, name })` guarantees an active scenario for the requested account, seeding a USD baseline plan when none exists.
- `persistBill(payload)` normalises and persists bills, rolling back optimistic changes when the API rejects the request.
- `removeBill(billId)` deletes a bill locally and forwards the deletion to the API when `mode === 'api'`.
- `persistScenarioAllocations(scenarioId, allocations)` writes allocation arrays and replaces them with the canonical API response once available.
- `setPlanningMode(mode)` toggles between `'local'` and `'api'` persistence strategies.
- `resetPlanningState(partial)` resets the singleton—useful in the Vitest suite.

Future E2E work should extend Cypress to interact with the composed view directly.

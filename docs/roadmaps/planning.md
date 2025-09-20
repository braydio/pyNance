# Planning & Allocation Roadmap

## Snapshot

- The Planning view (`frontend/src/views/Planning.vue`) is routed and wired to a local persistence layer through `frontend/src/services/planningService.ts` and the `usePlanning` composable.
- Flask routes live in `backend/app/routes/planning.py`, delegating to the in-memory service in `backend/app/services/planning_service.py`.
- Scenario-level API tests exist in `tests/test_api_planning.py`, exercising bill creation, allocation caps, and retrieval through a FastAPI harness that mirrors the Flask contract.

## Remaining work

### Frontend

1. **Component build-out**
   - **`frontend/src/components/planning/BillForm.vue`**
     - **Props:** accept an optional `bill?: Bill` to edit existing entries, a `currencyCode: string` sourced from the active scenario/account, and an optional `mode: 'create' | 'edit'` flag for button labels.
     - **Emits:** surface `update:bill` as the user types (so parents can persist a draft), `save` with a normalized payload (`amountCents` not decimals) once validation passes, and `cancel` when the modal closes.
     - **Shared helpers:** reuse `formatCurrency`/`convertCurrency` from `frontend/src/utils/currency.ts` plus a shared mapper that converts between the persisted `Bill` shape and editable form state.
     - **Remaining TODO:** replace the temporary reactive form + inline error strings with typed validation, migrate away from the JSON preview, and thread saved bills back through `usePlanning`/`updatePlanning` rather than leaving state patching to callers.
   - **`frontend/src/components/planning/BillList.vue`**
     - **Props:** receive `bills: Bill[]`, `currencyCode: string`, and an optional `selectedBillId` to highlight the active row.
     - **Emits:** fire `select` when a row is chosen, `edit` with the full bill payload, and `delete` with the identifier for removal confirmation.
     - **Shared helpers:** switch from the placeholder `@/utils/format` helper to `formatCurrency` for amount columns and reuse any shared empty-state renderer once it lands.
     - **Remaining TODO:** wire list actions to the planning service methods (optimistic updates will come later), replace inline `dueDate` fallbacks with a dedicated formatter, and remove the temporary styling stub.
   - **`frontend/src/components/planning/Allocator.vue`**
     - **Props:** take `categories: string[]`, a `modelValue: Record<string, number>` for `v-model`, and the `currencyCode: string` needed to format fixed allocation previews.
     - **Emits:** continue emitting `update:modelValue` for reactivity plus a richer `change` payload containing totals and validation booleans so parents can gate saves.
     - **Shared helpers:** centralize percentage math in a shared helper (e.g., `clampAllocations`) and rely on `formatCurrency` when displaying total allocated cash alongside the percent bars.
     - **Remaining TODO:** replace the inline `maxFor` computation with the shared helper once extracted and ensure errors flow back through a consistent toast/banner system instead of the placeholder paragraph.
   - **`frontend/src/components/planning/PlanningSummary.vue`**
     - **Props:** accept optional overrides for `scenarioId` and `currencyCode` so the summary can be reused in account dashboards while defaulting to the active scenario.
     - **Emits:** expose a `refresh` event hook (even if unused initially) to let parents force recomputation when cross-view data changes.
     - **Shared helpers:** continue using `usePlanning` alongside `selectActiveScenario`, `selectTotalBillsCents`, and `selectRemainingCents`, but route final strings through `formatCurrency` instead of the legacy formatter.
     - **Remaining TODO:** swap the hard-coded headings for design-system typography and replace the inline computed formatting with a shared selector once totals move server-side.
2. **Planning view composition**
   - Mount the four planning components within `frontend/src/views/Planning.vue`, sourcing state via `usePlanning()` and the selectors in `frontend/src/selectors/planning.ts` (e.g., hydrate `BillList` with `state.bills` filtered by the active scenario and feed `Allocator` with `selectActiveScenario(state)?.allocations`).
   - On mount, derive the active scenario/currency from planning state, load existing bills through `planningService.ts`, and pass a `currencyCode` prop to each child so they can delegate to `formatCurrency`/`convertCurrency` consistently.
   - Handle emitted events locally: call the planning service helpers on `save`/`delete`, update the reactive store via `updatePlanning`, and feed allocation changes back through selectors so `PlanningSummary` stays in sync.
   - Replace the JSON `<pre>` scaffold with the composed layout, leaving TODO comments where API wiring or optimistic updates are still pending so the remaining placeholder logic is obvious to implementers.
3. **Data synchronisation**
   - Extend `planningService.ts` with `listBills`, `createBill`, `updateBill`, and `deleteBill` calls that point at `/api/planning/bills` endpoints (feature flag for local vs. API mode).
   - Add optimistic updates with rollback on failure so the UI remains responsive offline.
4. **Validation & UX polish**
   - Enforce total allocation ≤ 100% with inline feedback, and surface predicted bill indicators.
   - Provide empty states and error toasts consistent with the design system.

### Backend

1. **Persistence & validation**
   - Replace in-memory stores with SQLAlchemy models once schema is finalised; enforce 100% allocation cap and bill uniqueness at the service layer.
   - Introduce schema validation using Marshmallow or Pydantic dataclasses to keep request handling explicit.
2. **Service coverage**
   - Expand tests around `planning_service.update_allocations` to cover concurrency and negative flows.
   - Ensure Flask blueprints raise `BadRequest`/`Conflict` with descriptive messages for failed validations.

### Quality & automation

- Augment Cypress specs in `frontend/src/views/__tests__/Planning.cy.js` (and Vue component specs where appropriate) to cover CRUD flows, allocation caps, and empty states.
- Keep backend tests hermetic by stubbing notification hooks; the existing FastAPI harness can be extended with additional cases before the Flask app is exercised end-to-end.
- Track code paths with coverage tooling—flag missing scenarios (e.g., deleting the last bill) for follow-up tests.

## Milestones

1. **M1 – Component scaffolding**: ship the four planning components with local persistence wired through the composable.
2. **M2 – API mode**: toggle to the Flask endpoints, add optimistic updates, and document the API contract in `docs/API_REFERENCE.md`.
3. **M3 – Validation polish**: enforce allocation/bill rules across backend and frontend with meaningful user feedback.
4. **M4 – Automated coverage**: ensure Cypress suites and backend tests cover CRUD, caps, and error paths.

_Last updated: 2025-09-10_

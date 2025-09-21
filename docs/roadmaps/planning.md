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
   - **Service contract:** Lean on the existing `planningService.ts` methods—`fetchBills`, `createBill`, `updateBill`, `deleteBill`, and the allocation helpers (`fetchAllocations`, `createAllocation`, `updateAllocation`, `deleteAllocation`)—as the single interface to `/api/planning/*` endpoints. Keep their Axios signatures stable so they can be mocked under unit tests.
   - **Composable orchestration:** Introduce async action helpers inside `usePlanning.ts` (e.g., `loadBills`, `persistBill`, `persistAllocationChange`) that call the service functions above. These helpers should mutate the reactive store exclusively through `updatePlanning` (or narrow mutations like `setActiveScenarioId`) so components never touch `state` directly.
   - **Feature flagging & modes:** Gate API usage behind a `planningMode` toggle (derived from `state.devMode`, a dedicated feature flag, or `import.meta.env.VITE_PLANNING_MODE`). When the toggle is `local`, the actions bypass network calls and fall back to `loadPlanning`/`savePlanning`; when `api`, they invoke the Axios helpers and sync the response payloads into the store.
   - **Optimistic flow:** When `api` mode is active, the composable actions should apply optimistic mutations to `state.bills`/`state.scenarios` via `updatePlanning`, stash the previous snapshot, and then call `createBill`/`updateBill`/`deleteBill` (and their allocation counterparts). On failure, roll back using the snapshot and surface the error to the caller; on success, merge the server response (e.g., persisted IDs, timestamps) back into the reactive arrays.
   - **State syncing & error propagation:** After every successful response, normalise the returned bill/allocation and overwrite the optimistic entry so selectors (like `selectActiveScenario`) see the canonical data. Bubble failures to the invoking components—`BillForm`, `BillList`, `Allocator`, etc.—either by rethrowing the caught error or returning a structured `{ error }` object so the UI can render toasts/banners consistently.
4. **Validation & UX polish**
   - Enforce total allocation ≤ 100% with inline feedback, and surface predicted bill indicators.
   - Provide empty states and error toasts consistent with the design system.

### Backend

1. **Persistence & validation**
   - Replace the in-memory service with the SQLAlchemy flow defined in `backend/app/models/planning_models.py` and `backend/app/sql/planning_logic.py`. Update `backend/app/routes/planning.py` to inject the new SQL-backed service, translate database exceptions into Flask `BadRequest`/`Conflict` responses, and serialise responses with the same schema used for request validation.
   - Introduce schema validation using Marshmallow or Pydantic dataclasses to keep request handling explicit, and ensure outbound payloads reuse the serializer so route responses stay in sync with the persisted models.
2. **Schema migrations**
   - Author Alembic migrations that create the `planning_scenarios`, `planned_bills`, and `scenario_allocations` tables. Store the migration scripts under `backend/migrations/versions/` with clear revision slugs and upgrade/downgrade paths that mirror the SQLAlchemy models.
3. **Service coverage**
   - Expand tests around `planning_service.update_allocations` to cover concurrency and negative flows.
   - Ensure Flask blueprints raise `BadRequest`/`Conflict` with descriptive messages for failed validations.
4. **Test updates**
   - Extend `tests/test_api_planning.py` to cover database-backed CRUD flows, schema validation failures, and enforcement of the 100% allocation cap.
   - Add Flask integration tests (or adapt existing FastAPI harness cases) that execute against the migrated schema to confirm persistence wiring, serialisation, and error translation once the SQL service is active.

### Quality & automation

- Augment Cypress specs in `frontend/src/views/__tests__/Planning.cy.js` (and Vue component specs where appropriate) to cover CRUD flows, allocation caps, and empty states.
- Keep backend tests hermetic by stubbing notification hooks; the existing FastAPI harness can be extended with additional cases before the Flask app is exercised end-to-end.
- Track code paths with coverage tooling—flag missing scenarios (e.g., deleting the last bill) for follow-up tests.

## Milestones

1. **M1 – Planning view composition (frontend foundation)**
   - **Deliverables**
     - Compose `frontend/src/views/Planning.vue` with `BillForm.vue`, `BillList.vue`, `Allocator.vue`, and `PlanningSummary.vue`, wiring selectors from `frontend/src/selectors/planning.ts` and local persistence through `frontend/src/composables/usePlanning.ts`.
     - Stub shared helpers in `frontend/src/utils/currency.ts` and any new allocation math utility to unblock follow-up refinements.
     - Add placeholder/unit scaffolding in `frontend/src/components/planning/__tests__/` (or extend `frontend/src/views/__tests__/Planning.cy.js`) to exercise event wiring and confirm local mode renders without API calls.
   - **Acceptance tests & docs**
     - Update Cypress smoke coverage to assert the composed view loads and can create/edit/delete bills using the local storage path.
     - Capture component notes in `docs/ui/planning.md` (or append to the existing planning section) outlining props/emits so backend/API contributors understand forthcoming integration points.
   - **Dependencies**
     - Establishes the baseline UI state required before API toggling (M2) and backend persistence (M3) can proceed.

2. **M2 – API mode enablement (service orchestration)**
   - **Deliverables**
     - Implement the `planningMode` toggle and async helpers inside `frontend/src/composables/usePlanning.ts` to call `frontend/src/services/planningService.ts` and reconcile optimistic updates.
     - Ensure `frontend/src/services/planningService.ts` covers all REST verbs used by the planning view, aligned with `backend/app/routes/planning.py` endpoints.
     - Document the request/response schema additions in `docs/API_REFERENCE.md` and, if introduced, add fixtures under `tests/fixtures/planning/`.
   - **Acceptance tests & docs**
     - Expand `tests/test_api_planning.py` to cover happy-path CRUD plus failure responses that the frontend will surface.
     - Add API-mode Cypress specs (or a Playwright alternative) verifying optimistic updates and fallback on API errors.
   - **Dependencies**
     - Builds on the composed frontend from M1 and unblocks backend persistence work in M3 by validating the contract surface.

3. **M3 – Persistence & validation hardening (backend-first)**
   - **Deliverables**
     - Replace the in-memory planning store with SQLAlchemy models under `backend/app/models/` and update `backend/app/services/planning_service.py` to enforce allocation caps and bill uniqueness.
     - Add Marshmallow/Pydantic schemas in `backend/app/schemas/planning.py` (or equivalent) and integrate them into `backend/app/routes/planning.py`.
     - Align frontend validation helpers in `frontend/src/composables/usePlanning.ts` and supporting components with backend rules to display consistent feedback.
   - **Acceptance tests & docs**
     - Extend backend unit/integration coverage (e.g., `tests/test_api_planning.py`, new `tests/test_planning_service.py`) for concurrency, rollback, and validation failures.
     - Update migration notes in `docs/backend/persistence.md` (or create the section) describing schema changes and rollout steps.
   - **Dependencies**
     - Requires the API contract from M2; once persistence is stable, QA automation (M4) can assert against real data flows.

4. **M4 – QA automation & regression safety (end-to-end)**
   - **Deliverables**
     - Broaden Cypress suites in `frontend/src/views/__tests__/Planning.cy.js` and component specs to cover CRUD, allocation caps, empty states, and error recovery using seeded backend data.
     - Add backend regression tests (pytest, contract tests) to guard against schema drift and ensure API compatibility with the frontend selectors.
     - Wire coverage reporting (e.g., Cypress code coverage plugin, pytest-cov) into CI configuration files under `.github/workflows/` or `scripts/`.
   - **Acceptance tests & docs**
     - Publish QA runbooks or updates in `docs/qa/planning-checklist.md`, detailing automation entry/exit criteria.
     - Record coverage thresholds and dashboards in `README.md` or `docs/roadmaps/qa.md` so contributors can track completion.
   - **Dependencies**
     - Depends on stable backend persistence (M3) and API-integrated frontend (M2); serves as the release gate for planning features.

_Last updated: 2024-05-29_

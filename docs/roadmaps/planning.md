# Planning & Allocation Roadmap

## Snapshot

- The Planning view (`frontend/src/views/Planning.vue`) is routed and wired to a persistence layer through `frontend/src/services/planningService.ts` and the `usePlanning` composable. The singleton now supports versioned local storage (v4) and an API mode toggle for optimistic sync.
- Flask routes live in `backend/app/routes/planning.py`, delegating to the in-memory service in `backend/app/services/planning_service.py`.
- Scenario-level API tests exist in `tests/test_api_planning.py`, exercising bill creation, allocation caps, and retrieval through a FastAPI harness that mirrors the Flask contract.

## Remaining work

### Frontend

**Status:** M1 (frontend foundation) delivered. The Planning view now renders the composed experience with persistent local state and documented contracts for backend integration.

- ✅ **`BillForm.vue`** now exposes `bill`, `currencyCode`, `mode`, and `visible` props, validates input with typed helpers from `frontend/src/utils/planning.ts`, and emits normalized `amountCents` payloads while broadcasting `update:bill` for draft persistence.
- ✅ **`BillList.vue`** renders formatted due dates and currency amounts via `formatCurrency`, highlights a selected bill, and surfaces `select`/`edit`/`delete` events that bubble up to the view.
- ✅ **`Allocator.vue`** drives percent distribution with the shared `clampAllocations` helper, emits structured change metadata (`totalPercent`, `totalCents`, `isValid`), and previews currency totals using the active scenario balance.
- ✅ **`PlanningSummary.vue`** consumes planning selectors to display bill totals, allocation summaries, and remaining cash with localized currency formatting while exposing a `refresh` hook.
- ✅ **`Planning.vue`** composes the four components, filters bills by the active scenario, persists changes through `usePlanning`, and seeds a default scenario when none exist. Local drafts, deletion confirmations, and allocation updates are all routed through the shared utilities so the upcoming API work can reuse the same surfaces.

**Next steps**

- ✅ Threaded API mode into `usePlanning` so the new components can swap between local storage and network persistence via `persistBill`, `removeBill`, and `persistScenarioAllocations`.
- Replace the optimistic `window.confirm` delete flow with a design-system modal once the shared dialog lands.
- Layer toast messaging for allocation validation and bill saves when the notification bus is introduced.
- Extend Cypress coverage to exercise the composed view; current unit suites validate selectors and component contracts, but end-to-end smoke coverage remains open.
3. **Data synchronisation**
   - **Service contract:** Lean on the existing `planningService.ts` methods—`fetchBills`, `createBill`, `updateBill`, `deleteBill`, and the allocation helpers (`fetchAllocations`, `createAllocation`, `updateAllocation`, `deleteAllocation`, plus the new `replaceScenarioAllocations`)—as the single interface to `/api/planning/*` endpoints. Keep their Axios signatures stable so they can be mocked under unit tests.
   - ✅ **Composable orchestration:** Async helpers inside `usePlanning.ts` (`ensureScenarioForAccount`, `persistBill`, `removeBill`, `persistScenarioAllocations`) now call the service layer and mutate the store exclusively through `updatePlanning`.
   - ✅ **Feature flagging & modes:** `PlanningState.mode` toggles between `'local'` and `'api'`, enabling API-driven flows without breaking local persistence.
   - ✅ **Optimistic flow:** API mode applies optimistic mutations, snapshots prior state, and rolls back on failure while merging canonical responses when successful.
   - ✅ **State syncing & error propagation:** Bill and allocation helpers normalise server payloads, replace optimistic entries, and rethrow errors so the UI can surface toast messaging in future polish passes.
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

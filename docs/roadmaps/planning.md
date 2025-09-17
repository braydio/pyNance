# Planning & Allocation Roadmap

## Snapshot

- The Planning view (`frontend/src/views/Planning.vue`) is routed and wired to a local persistence layer through `frontend/src/services/planningService.ts` and the `usePlanning` composable.
- Flask routes live in `backend/app/routes/planning.py`, delegating to the in-memory service in `backend/app/services/planning_service.py`.
- Scenario-level API tests exist in `tests/test_api_planning.py`, exercising bill creation, allocation caps, and retrieval through a FastAPI harness that mirrors the Flask contract.

## Remaining work

### Frontend

1. **Component build-out**
   - Implement `frontend/src/components/planning/BillForm.vue`, `BillList.vue`, `Allocator.vue`, and `PlanningSummary.vue` with composition API + TypeScript props.
   - Replace the placeholder currency helpers by exporting `formatCurrency` and `convertCurrency` utilities from `frontend/src/utils/currency.ts`.
2. **Data synchronisation**
   - Extend `planningService.ts` with `listBills`, `createBill`, `updateBill`, and `deleteBill` calls that point at `/api/planning/bills` endpoints (feature flag for local vs. API mode).
   - Add optimistic updates with rollback on failure so the UI remains responsive offline.
3. **Validation & UX polish**
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

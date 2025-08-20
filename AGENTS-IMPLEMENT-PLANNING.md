# Planning Module Implementation Guide

This document consolidates `AGENT-IMPLEMENT.md` and `AGENT-FINAL.md` into a single, repo-accurate plan for the budgeting and allocation feature.

## Already Implemented
- Backend models, service, and routes for planning scenarios are present in:
  - `backend/app/models.py`
  - `backend/app/services/planning_service.py`
  - `backend/app/routes/planning.py`
- Frontend scaffolding includes:
  - Type definitions in `frontend/src/types/planning.ts`
  - Local persistence in `frontend/src/services/planningService.ts`

## Superseded or Incorrect Directions
- **Typing**: prior spec forbade `src/types`; the project already uses dedicated TypeScript definitions.
- **File Names**: `.js` targets should be `.ts` (`planningService.ts`, `utils/currency.ts`).
- **Testing**: Jest/Vue Test Utils instructions are replaced by Cypress component tests.
- **Currency Utility**: existing `utils/currency.ts` contains only types and must be replaced with conversion helpers.

## Remaining Implementation Tasks

### Frontend
1. Add `frontend/src/composables/usePlanning.ts` (singleton state using `PlanningState`).
2. Create `frontend/src/views/Planning.vue` and register route `/planning` in `frontend/src/router/index.js` with a sidebar link.
3. Implement components under `frontend/src/components/planning/`:
   - `BillForm.vue`
   - `BillList.vue`
   - `Allocator.vue`
   - `PlanningSummary.vue`
4. Replace `frontend/src/utils/currency.ts` with:
   ```ts
   export const toCents = (n: number | string) => Math.round(Number(n || 0) * 100);
   export const fromCents = (c: number) => Number(c || 0) / 100;
   export const formatCurrency = (
     cents: number,
     locale = "en-US",
     currency = "USD"
   ) => new Intl.NumberFormat(locale, { style: "currency", currency }).format(fromCents(cents));
   ```
5. Extend `frontend/src/services/planningService.ts` with list/get/put helpers supporting future API mode.
6. Add Cypress component tests at `frontend/src/views/__tests__/Planning.cy.js` covering balance updates, bill CRUD, and allocation math.

### Backend
1. Ensure planning routes scope data to the authenticated user and require login.
2. Consolidate duplicated models (`backend/app/models.py` vs `backend/app/models/planning_models.py`) into a single module.
3. Write `tests/test_api_planning.py` validating scenario CRUD, percent-cap enforcement, and user isolation.

## Allocation Rules
- Apply fixed allocations first; percent allocations operate on remaining balance with a total cap of 100%.
- Remaining balance cannot drop below zero.
- Predicted bills are regenerated in dev mode and tagged visually.

## Milestones
- **M1 – Scaffolding**: route, view, composable, and persistence wired.
- **M2 – Bills**: add/edit/delete bills; predicted flags shown.
- **M3 – Allocator**: manage fixed and percent allocations with clamped remaining balance.
- **M4 – Dev Mode**: toggle persists and replaces predicted bills.
- **M5 – Tests**: backend API and frontend component tests pass.

# Planning Module Implementation Guide

This document consolidates previous agent instructions into the authoritative roadmap for the budgeting and allocation feature.

## Status Checklist

### Frontend
- [x] `frontend/src/types/planning.ts`
- [x] `frontend/src/services/planningService.ts` (local persistence)
- [x] `frontend/src/composables/usePlanning.ts`
 - [x] `frontend/src/views/Planning.vue` with `/planning` route and sidebar link
 - [ ] `frontend/src/components/planning/` (`BillForm.vue`, `BillList.vue`, `Allocator.vue`, `PlanningSummary.vue`)
- [ ] Replace `frontend/src/utils/currency.ts` with conversion helpers
- [ ] Extend `frontend/src/services/planningService.ts` with list/get/put helpers for future API mode
- [ ] Cypress component tests at `frontend/src/views/__tests__/Planning.cy.js`

### Backend
- [x] Models (`backend/app/models/planning_models.py`)
- [x] Service (`backend/app/services/planning_service.py`)
- [x] Routes (`backend/app/routes/planning.py`)
- [ ] Require login and scope data to `current_user`
- [ ] `tests/test_api_planning.py` for scenario CRUD, percent-cap enforcement, and user isolation

## Superseded or Incorrect Directions
- **Typing**: prior spec forbade `src/types`; the project uses dedicated TypeScript definitions.
- **File Names**: `.js` targets should be `.ts` (`planningService.ts`, `utils/currency.ts`).
- **Testing**: Jest/Vue Test Utils instructions are replaced by Cypress component tests.
- **Currency Utility**: existing `utils/currency.ts` contains only types and must be replaced with conversion helpers.

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

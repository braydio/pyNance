# 🧮 Roadmap: Planning Module

## 1. Current Status
- Types, service, and composable implemented.
- View scaffolded with route and navigation link.

## 2. Frontend
### 2.1 Upcoming Components
- `frontend/src/components/planning/` (`BillForm.vue`, `BillList.vue`, `Allocator.vue`, `PlanningSummary.vue`)
- Replace `frontend/src/utils/currency.ts` with conversion helpers
- Extend `frontend/src/services/planningService.ts` with list/get/put helpers for future API mode
- Cypress component tests at `frontend/src/views/__tests__/Planning.cy.js`

## 3. Backend
- Require login and scope data to `current_user`
- `tests/test_api_planning.py` for scenario CRUD, percent-cap enforcement, and user isolation

## 4. Next Steps
1. Implement bill management components and integrate into Planning view.
2. Add currency conversion utilities and API-ready service helpers.
3. Enforce authentication in planning routes and add backend tests.
4. Create Cypress component tests for the Planning view.

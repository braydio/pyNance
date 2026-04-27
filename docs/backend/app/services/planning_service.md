# `planning_service.py`

## Responsibility

- Persist Planning scenarios, bills, and allocation targets through SQLAlchemy.
- Validate frontend API payloads and return canonical camelCase response shapes.
- Enforce scenario-level percent allocation totals at or below 100%.

## Key Functions

- [`list_scenarios()`](../../../../backend/app/services/planning_service.py): Return persisted scenarios with embedded allocations.
- [`create_scenario(data)`](../../../../backend/app/services/planning_service.py): Create a scenario using `name`, `accountId`, `planningBalanceCents`, and `currencyCode`.
- [`get_bills()`](../../../../backend/app/services/planning_service.py) / [`create_bill(data)`](../../../../backend/app/services/planning_service.py) / [`update_bill(bill_id, data)`](../../../../backend/app/services/planning_service.py) / [`delete_bill(bill_id)`](../../../../backend/app/services/planning_service.py): Manage durable bill records.
- [`get_allocations(scenario_id)`](../../../../backend/app/services/planning_service.py) / [`create_allocation(scenario_id, data)`](../../../../backend/app/services/planning_service.py) / [`update_allocation(scenario_id, allocation_id, data)`](../../../../backend/app/services/planning_service.py) / [`delete_allocation(scenario_id, allocation_id)`](../../../../backend/app/services/planning_service.py): Manage scenario-scoped allocation records.
- [`replace_allocations(scenario_id, allocations)`](../../../../backend/app/services/planning_service.py): Replace the full allocation list used by the frontend optimistic API mode.

## Contract Notes

- Request and response payloads intentionally match `frontend/src/types/planning.ts`.
- Bills use `amountCents`, `dueDate`, `accountId`, and `scenarioId` at the API boundary; the service maps those fields to snake_case model columns.
- Allocation `kind` must be `fixed` or `percent`; percent values are validated both individually and in aggregate.
- Missing resources raise `NotFound`; malformed payloads raise `BadRequest`.

## Dependencies & Collaborators

- `app.extensions.db`
- `app.models.PlanningScenario`
- `app.models.PlannedBill`
- `app.models.ScenarioAllocation`
- `frontend/src/services/planningService.ts`

## Tests

- `tests/test_api_planning.py` covers scenario creation, bill CRUD, validation failures, and scenario allocation cap enforcement.

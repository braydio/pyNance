# `planning_service.py`

## Responsibility
- Maintain an in-memory prototype of budgeting data structures for bills and allocation percentages.
- Provide CRUD utilities that power early planning UI experiments.

## Key Functions
- [`get_bills()`](../../../../backend/app/services/planning_service.py) / [`create_bill(bill)`](../../../../backend/app/services/planning_service.py) / [`update_bill(bill_id, bill)`](../../../../backend/app/services/planning_service.py) / [`delete_bill(bill_id)`](../../../../backend/app/services/planning_service.py): Read and mutate the ephemeral `BILLS` list.
- [`get_allocations()`](../../../../backend/app/services/planning_service.py) / [`update_allocations(allocations)`](../../../../backend/app/services/planning_service.py): Expose and replace allocation data while enforcing a 100% aggregate cap.

## Dependencies & Collaborators
- Operates purely in memory—no database or external service dependencies.
- Intended as a lightweight partner for eventual persistence logic in the planning suite (e.g., SQL counterparts once implemented).

## Usage Notes
- Because the store is process-local, data is reset on application restarts; callers should treat it as non-durable test scaffolding.
- `update_allocations` raises `ValueError` when provided percentages exceed 100, protecting UI workflows from inconsistent totals.

# Planning Route (`planning.py`)

## Purpose

Provide CRUD endpoints for budgeting and bill planning artifacts, delegating validation and storage to `planning_service`.

## Endpoints

- `GET /api/planning/bills` – Return the list of planned bills.
- `POST /api/planning/bills` – Create a bill using the provided JSON body.
- `PUT /api/planning/bills/<bill_id>` – Update a bill by ID.
- `DELETE /api/planning/bills/<bill_id>` – Delete a bill.
- `GET /api/planning/allocations` – Fetch allocation targets for the planning UI.
- `PUT /api/planning/allocations` – Replace allocation targets.

## Inputs/Outputs

- **Bill endpoints**
  - **Inputs:** JSON bodies describing bills; missing bodies raise `BadRequest`.
  - **Outputs:** Raw JSON lists/dicts for reads; created resources return `(payload, status)` tuples with HTTP 201.
- **Allocations endpoints**
  - **Inputs:** JSON allocation targets validated for 100% caps.
  - **Outputs:** Updated allocation payload or error details when validation fails.

## Auth

- Requires authenticated user; planning data is scoped per user context.

## Dependencies

- `app.services.planning_service` functions for bill CRUD and allocation updates.

## Behaviors/Edge Cases

- Persistence is in-memory in current implementation; data resets on process restart.
- `update_allocations` propagates `ValueError` when totals exceed allowed percentages.

## Sample Request/Response

```http
POST /api/planning/bills HTTP/1.1
Content-Type: application/json

{ "name": "Rent", "amount": 1200, "due_day": 1 }
```

```json
{ "name": "Rent", "amount": 1200, "due_day": 1 }
```

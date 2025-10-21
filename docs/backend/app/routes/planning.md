# Planning Route

## Purpose

Offers CRUD endpoints for financial planning artifacts that power the budgeting
views. Request handling is thin: JSON payloads are validated for presence and
then delegated to `app.services.planning_service`, which currently stores data
in memory for ease of testing.

## Key Endpoints

- `GET /api/planning/bills` – Return the full list of planned bills.
- `POST /api/planning/bills` – Create a bill using the JSON body forwarded to
  `planning_service.create_bill`.
- `PUT /api/planning/bills/<bill_id>` – Update a bill by ID with the provided
  payload.
- `DELETE /api/planning/bills/<bill_id>` – Remove a bill and acknowledge the
  deletion.
- `GET /api/planning/allocations` – Fetch the allocation targets used by the
  planning UI.
- `PUT /api/planning/allocations` – Replace allocation targets, delegating the
  validation (including the 100% cap) to `planning_service.update_allocations`.

## Inputs & Outputs

- All mutating endpoints require a JSON body; missing bodies raise a `BadRequest`.
- Responses return bare JSON payloads for reads and `(payload, status)` tuples
  for creates.
- `update_allocations` propagates any `ValueError` raised by the service (for
  example when percentages exceed 100%), which surfaces as an error response to
  the client.

## Internal Dependencies

- `app.services.planning_service.get_bills`
- `app.services.planning_service.create_bill`
- `app.services.planning_service.update_bill`
- `app.services.planning_service.delete_bill`
- `app.services.planning_service.get_allocations`
- `app.services.planning_service.update_allocations`

## Known Behaviors

- Because persistence is in-memory, data resets when the process restarts.
- Endpoints return minimal envelopes (raw lists/dicts) so callers should handle
  presentation formatting.

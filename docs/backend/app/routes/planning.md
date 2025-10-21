# `planning.py`

REST endpoints for the financial planning workspace. The blueprint is registered
under `/api/planning` and proxies almost all persistence logic to
`app.services.planning_service`.

## Dependencies

- `app.services.planning_service.get_bills`, `.create_bill`, `.update_bill`,
  `.delete_bill`
- `app.services.planning_service.get_allocations` and `.update_allocations`
- Raises `werkzeug.exceptions.BadRequest` when JSON bodies are missing.

## Endpoints

| Method | Path | Description |
| ------ | ---- | ----------- |
| `GET` | `/api/planning/bills` | Returns the list of stored bill definitions. |
| `POST` | `/api/planning/bills` | Accepts a JSON body and forwards it to `create_bill`; returns the created bill with a 201 status. |
| `PUT` | `/api/planning/bills/<bill_id>` | Updates the referenced bill by delegating to `update_bill`. |
| `DELETE` | `/api/planning/bills/<bill_id>` | Removes the bill and returns `{ "status": "deleted" }`. |
| `GET` | `/api/planning/allocations` | Retrieves allocation targets for planned budgets. |
| `PUT` | `/api/planning/allocations` | Replaces the allocation collection using `update_allocations`. |

## Notes

- All endpoints expect and return JSON payloads.
- Validation is intentionally light: the service layer is responsible for
  enforcing schema/field semantics.
- Tests typically patch `planning_service` to isolate route behaviour.

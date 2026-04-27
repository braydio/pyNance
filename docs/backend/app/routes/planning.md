---
Owner: Backend Team
Last Updated: 2026-04-26
Status: Active
---

# Planning Route (`planning.py`)

## Purpose
Provide CRUD endpoints for budgeting and bill planning artifacts, delegating validation and storage to `planning_service`.

## Endpoints
- `GET /api/planning/scenarios` – Return persisted planning scenarios.
- `POST /api/planning/scenarios` – Create a planning scenario.
- `GET /api/planning/bills` – Return the list of planned bills.
- `POST /api/planning/bills` – Create a bill using the provided JSON body.
- `PUT /api/planning/bills/<bill_id>` – Update a bill by ID.
- `DELETE /api/planning/bills/<bill_id>` – Delete a bill.
- `GET /api/planning/scenarios/<scenario_id>/allocations` – Fetch scenario allocation targets.
- `POST /api/planning/scenarios/<scenario_id>/allocations` – Create one allocation target.
- `PUT /api/planning/scenarios/<scenario_id>/allocations` – Replace all allocation targets for the scenario.
- `PUT /api/planning/scenarios/<scenario_id>/allocations/<allocation_id>` – Update one allocation target.
- `DELETE /api/planning/scenarios/<scenario_id>/allocations/<allocation_id>` – Delete one allocation target.

## Inputs/Outputs
- **Bill endpoints**
  - **Inputs:** Frontend contract fields from `frontend/src/types/planning.ts`: `name`, `amountCents`, `dueDate`, `frequency`, `category`, `origin`, `accountId`, and `scenarioId`.
  - **Outputs:** CamelCase JSON payloads matching the frontend `Bill` type; created resources return HTTP 201.
- **Allocations endpoints**
  - **Inputs:** `{ "target": string, "kind": "fixed"|"percent", "value": number }` objects.
  - **Outputs:** Canonical allocation payloads with server-generated UUIDs. Percent allocations are capped at 100% per scenario.

## Auth
- Current endpoints do not enforce user authentication yet. Scenario/account scoping is represented in payload fields and should be tightened before multi-user deployment.

## Dependencies
- `app.services.planning_service` functions for bill CRUD and allocation updates.

## Behaviors/Edge Cases
- Data persists through SQLAlchemy models: `PlanningScenario`, `PlannedBill`, and `ScenarioAllocation`.
- Missing JSON bodies raise `BadRequest`.
- Unknown scenario, bill, and allocation IDs raise `NotFound`.
- Percent allocation totals above 100 return `BadRequest`.

## Sample Request/Response
```http
POST /api/planning/bills HTTP/1.1
Content-Type: application/json

{
  "name": "Rent",
  "amountCents": 120000,
  "dueDate": "2026-05-01",
  "frequency": "monthly",
  "category": "Housing",
  "origin": "manual",
  "accountId": "checking-1",
  "scenarioId": "0f99b98d-6905-4eca-a7ea-e7d26beab7a9"
}
```

```json
{
  "id": "dc56446f-1b44-49b4-8be1-d72424574546",
  "name": "Rent",
  "amountCents": 120000,
  "dueDate": "2026-05-01",
  "frequency": "monthly",
  "category": "Housing",
  "origin": "manual",
  "accountId": "checking-1",
  "scenarioId": "0f99b98d-6905-4eca-a7ea-e7d26beab7a9"
}
```

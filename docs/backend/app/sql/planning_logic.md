# backend/app/sql/planning_logic.py

## Purpose

Provide CRUD helpers and validation for Planning scenarios, planned bills, and
allocation rules.

## Key Responsibilities

- Create, update, list, and delete planning scenarios.
- Validate due dates, allocation constraints, and bill/allocations payloads.

## Primary Functions

- `parse_due_date(raw)`
  - Parses `YYYY-MM-DD` strings into `date` or raises `BadRequest`.
- `validate_percent_cap(scenario)`
  - Ensures percent allocations do not exceed 100%.
- `list_scenarios()`
  - Returns scenarios ordered by creation date.
- `get_scenario(scenario_id)`
  - Fetches a single scenario by UUID.
- `create_scenario(name)`
  - Validates name, creates, commits.
- `update_scenario(scenario_id, data)`
  - Replaces bills and allocations, validates inputs, commits.
- `delete_scenario(scenario_id)`
  - Deletes a scenario by UUID, commits.

## Inputs

- Scenario name, UUIDs, and payload dicts for bills/allocations.

## Outputs

- `PlanningScenario` instances or `None` depending on helper.

## Internal Dependencies

- `app.models.PlanningScenario`, `PlannedBill`, `ScenarioAllocation`
- `app.extensions.db`
- `werkzeug.exceptions.BadRequest`, `NotFound`

## Known Behaviors

- `update_scenario` clears existing bills and allocations before replacing them.
- Invalid bill names, amounts, or allocation kinds raise `BadRequest`.

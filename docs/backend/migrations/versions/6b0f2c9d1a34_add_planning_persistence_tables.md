# Migration `6b0f2c9d1a34` — add Planning persistence tables

## Summary

Creates durable SQL tables for the Planning API so bills, scenarios, and allocation targets no longer live in process-local memory.

## Schema Changes

- `planning_scenarios`
  - UUID primary key.
  - Scenario name, optional account scope, planning balance in cents, currency code, and timestamps.
- `planned_bills`
  - UUID primary key.
  - Scenario foreign key with cascade delete.
  - Bill name, amount in cents, due date, frequency, category, origin, optional account scope, predicted flag, and timestamps.
- `scenario_allocations`
  - UUID primary key.
  - Scenario foreign key with cascade delete.
  - Target, allocation kind (`fixed` or `percent`), value, and timestamps.
  - Check constraint for fixed non-negative values and percent values from 0 to 100.

## Rationale

The Planning frontend already supports API mode and optimistic persistence. This migration supplies the durable storage needed by `backend/app/services/planning_service.py` and the scenario-scoped allocation routes.

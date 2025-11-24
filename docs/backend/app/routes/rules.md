# Rules Route (`rules.py`)

## Purpose
Expose CRUD operations for transaction rules that automate categorization and metadata enrichment while persisting changes through SQL helpers.

## Endpoints
- `GET /api/rules/` – Return active rules for a user in creation order.
- `POST /api/rules/` – Create a rule for the provided user.
- `PATCH /api/rules/<rule_id>` – Partially update a rule's criteria, action, or active flag.
- `DELETE /api/rules/<rule_id>` – Remove a rule record.

## Inputs/Outputs
- **GET /api/rules/**
  - **Inputs:** Query parameter `user_id`.
  - **Outputs:** `{ "status": "success", "data": [ ...rules ] }` scoped to the user.
- **POST /api/rules/**
  - **Inputs:** JSON payloads with `match_criteria` and `action` dictionaries.
  - **Outputs:** `{ "status": "success", "data": { ...created_rule } }`.
- **PATCH /api/rules/<rule_id>` / `DELETE /api/rules/<rule_id>`**
  - **Inputs:** Path parameter `rule_id` and partial rule body for PATCH.
  - **Outputs:** Success envelopes or 4xx errors for missing/not-found identifiers.

## Auth
- Requires authenticated user context; all rules are scoped by `user_id`.

## Dependencies
- `app.sql.transaction_rules_logic` helpers for create/update/list logic.
- `app.models.TransactionRule` and `app.extensions.db` for persistence.

## Behaviors/Edge Cases
- Updates normalize `is_active` using `bool(...)` to handle truthy inputs.
- Endpoints reject missing `user_id` to ensure correct scoping.

## Sample Request/Response
```http
POST /api/rules/ HTTP/1.1
Content-Type: application/json

{ "user_id": 1, "match_criteria": { "merchant": "Target" }, "action": { "category_id": "shopping" } }
```

```json
{ "status": "success", "data": { "id": 10, "is_active": true } }
```

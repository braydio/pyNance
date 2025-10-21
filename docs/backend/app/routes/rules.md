# Rules Route

## Purpose

Expose CRUD operations for transaction rules that automate categorization and
metadata enrichment. The routes coordinate with the SQL helper module so changes
are persisted consistently.

## Key Endpoints

- `GET /api/rules/` – Require a `user_id` query param and return active rules in
  creation order.
- `POST /api/rules/` – Accept a JSON payload to create a rule for the given
  user.
- `PATCH /api/rules/<rule_id>` – Partially update a rule's criteria, action, or
  active flag.
- `DELETE /api/rules/<rule_id>` – Remove the rule record.

## Inputs & Outputs

- Payloads use `match_criteria` and `action` dictionaries mirroring the
  structure consumed by `transaction_rules_logic.apply_rules`.
- Responses wrap results in `{ "status": "success", ... }` and surface 4xx
  errors for missing identifiers or not-found cases.

## Internal Dependencies

- `app.sql.transaction_rules_logic.create_rule`
- `app.sql.transaction_rules_logic.get_applicable_rules`
- `app.models.TransactionRule`
- `app.extensions.db`

## Known Behaviors

- Updates toggle `is_active` using `bool(...)` to normalize truthy inputs.
- Create/list endpoints enforce the presence of a `user_id` to scope results.

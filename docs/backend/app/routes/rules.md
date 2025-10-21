# `rules.py`

Automation rules that post-process imported transactions. Blueprint registered
at `/api/rules`.

## Dependencies

- `app.sql.transaction_rules_logic` – bulk retrieval and creation helpers.
- `app.models.TransactionRule` – SQLAlchemy model for persistence.
- `app.extensions.db` – commit/rollback management.

## Endpoints

| Method   | Path                   | Description                                                                                                                         |
| -------- | ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `GET`    | `/api/rules/`          | Requires `user_id` query parameter; returns active rules produced by `transaction_rules_logic.get_applicable_rules`.                |
| `POST`   | `/api/rules/`          | Creates a rule by delegating to `transaction_rules_logic.create_rule`. Expects JSON with `user_id`, `match_criteria`, and `action`. |
| `PATCH`  | `/api/rules/<rule_id>` | Updates mutable fields (`match_criteria`, `action`, `is_active`) on the referenced rule.                                            |
| `DELETE` | `/api/rules/<rule_id>` | Permanently deletes the rule.                                                                                                       |

## Validation & Errors

- Missing `user_id` for list/create requests returns `400` with a message.
- Non-existent rule IDs yield `404` responses from PATCH/DELETE.
- Successful writes respond with `{ "status": "success" }` (and `data.id` on create).

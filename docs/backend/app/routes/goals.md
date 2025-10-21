# `goals.py`

CRUD surface for high-level financial goals. The blueprint is registered at
`/api/goals`.

## Dependencies

- `app.models.FinancialGoal` – SQLAlchemy model providing persistence.
- `app.extensions.db` – session management for commit/rollback.
- `datetime` for parsing ISO `YYYY-MM-DD` due dates.

## Endpoints

| Method | Path         | Description                                                                                                                                                      |
| ------ | ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GET`  | `/api/goals` | Returns all stored goals with account, user, and metadata fields.                                                                                                |
| `POST` | `/api/goals` | Creates a goal from the posted JSON payload. Required fields: `account_id`, `due_date`. Optional fields include `user_id`, `name`, `target_amount`, and `notes`. |

## Validation & Error Handling

- Missing or malformed fields raise `KeyError`/`ValueError`; the route traps
  these and returns a `400` with the error message.
- Successful writes respond with `{ "status": "success", "id": <goal_id> }`.
- Dates must be provided as ISO strings (`YYYY-MM-DD`).

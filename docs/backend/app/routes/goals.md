# Goals Route

## Purpose

Expose endpoints for CRUD-style management of user financial goals stored in the
`FinancialGoal` model. The blueprint currently supports listing existing goals
and inserting new ones.

## Key Endpoints

- `GET /api/goals` – Return all financial goals belonging to the authenticated
  scope. Results are wrapped with `status` and `data` keys.
- `POST /api/goals` – Accept a JSON payload describing the goal and persist a new
  `FinancialGoal` row.

## Inputs & Outputs

- Requests must supply `user_id`, `account_id`, `due_date` (`YYYY-MM-DD`), and
  `target_amount`; missing or malformed fields trigger a `400` response with the
  exception message before reaching the database.
- Successful creates respond with `{ "status": "success", "id": <pk> }` and
  HTTP 201.

## Internal Dependencies

- `app.models.FinancialGoal` for the ORM mapping
- `app.extensions.db` for persistence

## Known Behaviors

- Goals are timestamped via SQLAlchemy mixins, enabling chronological reporting
  in downstream analytics.
- `due_date` is parsed with `datetime.strptime(..., "%Y-%m-%d")`; callers must
  conform to this format.

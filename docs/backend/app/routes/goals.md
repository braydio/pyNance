# Goals Route (`goals.py`)

## Purpose
Manage CRUD operations for user financial goals stored in the `FinancialGoal` model.

## Endpoints
- `GET /api/goals` – Return all financial goals for the authenticated user.
- `POST /api/goals` – Create a new financial goal from the provided payload.

## Inputs/Outputs
- **GET /api/goals**
  - **Inputs:** None beyond authenticated user context.
  - **Outputs:** `{ "status": "success", "data": [ ...goals ] }`.
- **POST /api/goals**
  - **Inputs:** JSON body with `user_id`, `account_id`, `due_date` (`YYYY-MM-DD`), and `target_amount`.
  - **Outputs:** `{ "status": "success", "id": <pk> }` with HTTP 201 on success; validation errors return 400 with message.

## Auth
- Requires authenticated user; all operations are scoped to that user.

## Dependencies
- `app.models.FinancialGoal` ORM model.
- `app.extensions.db` for persistence.

## Behaviors/Edge Cases
- `due_date` must follow `YYYY-MM-DD` and is parsed with `datetime.strptime`.
- Goals inherit timestamp mixins for chronological reporting.

## Sample Request/Response
```http
POST /api/goals HTTP/1.1
Content-Type: application/json

{ "user_id": 1, "account_id": 2, "due_date": "2025-12-31", "target_amount": 5000 }
```

```json
{ "status": "success", "id": 42 }
```

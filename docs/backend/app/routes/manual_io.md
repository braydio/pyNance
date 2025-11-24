# Manual IO Route (`manual_io.py`)

## Purpose
Allow manual creation, update, and deletion of transactions to supplement imported financial data.

## Endpoints
- `POST /manual` – Add a new manual transaction.
- `GET /manual` – Retrieve all manual entries.
- `PATCH /manual/<id>` – Update a specific manual transaction.
- `DELETE /manual/<id>` – Delete a manual entry.

## Inputs/Outputs
- **POST /manual**
  - **Inputs:** Transaction payload including `amount`, `date`, `description`, `category`, and `account_id`.
  - **Outputs:** Newly created transaction object with server-assigned `id`.
- **GET /manual**
  - **Inputs:** None.
  - **Outputs:** Array of manual transaction objects.
- **PATCH /manual/<id>**
  - **Inputs:** Partial transaction updates (e.g., `description`, `amount`).
  - **Outputs:** Updated transaction object.
- **DELETE /manual/<id>**
  - **Inputs:** Path parameter `id`.
  - **Outputs:** `{ "success": true }` on deletion.

## Auth
- Requires authenticated user; manual entries are scoped to the user's accounts.

## Dependencies
- `models.Transaction` for persistence.
- `services.manual_transaction_service` plus validation and ID helpers.

## Behaviors/Edge Cases
- Manual entries are stored separately from imports but merge into charts and summaries.
- Edits remain auditable through transaction history.

## Sample Request/Response
```http
POST /manual HTTP/1.1
Content-Type: application/json

{ "amount": 34.2, "date": "2024-12-10", "description": "Lunch - Cash", "category": "Food", "account_id": "acct_001" }
```

```json
{ "id": "manual_123", "amount": 34.2, "date": "2024-12-10", "description": "Lunch - Cash" }
```

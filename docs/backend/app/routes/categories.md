# Categories Route (`categories.py`)

## Purpose
Manage transaction categorization workflows, including listing categories, applying category updates, and maintaining rule-based tagging.

## Endpoints
- `GET /categories` – Fetch default and user-defined categories.
- `GET /categories/tree` – Provide nested category/detail relationships.
- `POST /categories/update` – Update category metadata.
- `POST /categories/apply` – Reassign category tags to transactions.
- `GET /rules` – List saved transaction rules.
- `POST /rules` – Create a new rule.
- `PATCH /rules/<id>` – Modify or disable a rule.
- `DELETE /rules/<id>` – Remove a rule.

## Inputs/Outputs
- **GET /categories**
  - **Inputs:** None.
  - **Outputs:** Full list of system and custom categories.
- **GET /categories/tree**
  - **Inputs:** None.
  - **Outputs:** Tree payload `{ "status": "success", "data": [{ "name": str, "children": [{ "id": int, "name": str }] }] }`.
- **POST /categories/update**
  - **Inputs:** `{ "category_id": str, "label": str, "emoji"?: str }`.
  - **Outputs:** Updated category object.
- **POST /categories/apply**
  - **Inputs:** `{ "transaction_ids": [str], "category_id": str }`.
  - **Outputs:** `{ "success": boolean, "updated": int }` summarizing updates.
- **Rule endpoints**
  - **Inputs:** Rule criteria or partial updates depending on verb.
  - **Outputs:** Rule objects or `{ "success": boolean }` after deletion.

## Auth
- Requires authenticated user context; categories and rules are scoped to the user's data.

## Dependencies
- `models.Category` for persistence.
- `services.categorization_service` and validation utilities.

## Behaviors/Edge Cases
- Automatic assignment uses merchant rules; manual overrides persist across syncs.
- Enforces duplicate-label protection and allows deactivating rules without deletion.

## Sample Request/Response
```http
POST /categories/apply HTTP/1.1
Content-Type: application/json

{ "transaction_ids": ["txn_1", "txn_2"], "category_id": "cat_groceries" }
```

```json
{ "success": true, "updated": 2 }
```

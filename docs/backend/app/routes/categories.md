## 📘 `categories.py`

```markdown
# Categories Route

## Purpose

Manages transaction categorization logic and user-defined category updates. Supports automatic and manual tagging workflows.

## Key Endpoints

- `GET /categories`: Fetch default and user-defined categories.
- `POST /categories/update`: Update category metadata (e.g., label, emoji).
- `POST /categories/apply`: Reassign category tags to transactions.
- `GET /categories/tree`: Nested view of primary and detailed categories.
- `GET /rules`: List saved transaction rules.
- `POST /rules`: Create a new rule.
- `PATCH /rules/<id>`: Modify or disable a rule.
- `DELETE /rules/<id>`: Remove a rule.

## Inputs & Outputs

- **GET /categories**

  - **Output:** List of all categories, including system and custom types.

- **GET /categories/tree**

  - **Output:** `{ status: 'success', data: [{ name: str, children: [{ id: int, name: str }] }] }`
  - Useful for populating dropdown menus.

- **POST /categories/update**

  - **Input:** `{ category_id: str, label: str, emoji?: str }`
  - **Output:** Updated category object.

- **POST /categories/apply**
  - **Input:** `{ transaction_ids: [str], category_id: str }`
  - **Output:** `{ success: boolean, updated: int }`
- **GET /rules**
  - **Output:** List of saved rules.
- **POST /rules**
  - **Input:** { match_criteria: {...}, action: {...} }
  - **Output:** Newly created rule object.
- **PATCH /rules/<id>**
  - **Input:** Partial updates or { is_active: bool }
  - **Output:** Updated rule object.
- **DELETE /rules/<id>**
  - **Output:** { success: boolean }

## Internal Dependencies

- `models.Category`
- `services.categorization_service`
- Validation schema utilities

## Known Behaviors

- Automatic category assignment based on merchant rules.
- Manual overrides persist across syncs.
- Duplicate protection on category labels.

## Related Docs

- [`docs/backend/services/categorization_service.md`](../services/categorization_service.md)
- [`docs/dataflow/categorization_pipeline.md`](../../dataflow/categorization_pipeline.md)
```

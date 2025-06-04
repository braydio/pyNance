## 📘 `categories.py`

```markdown
# Categories Route

## Purpose

Manages transaction categorization logic and user-defined category updates. Supports automatic and manual tagging workflows.

## Key Endpoints

- `GET /categories`: Fetch default and user-defined categories.
- `POST /categories/update`: Update category metadata (e.g., label, emoji).
- `POST /categories/apply`: Reassign category tags to transactions.

## Inputs & Outputs

- **GET /categories**

  - **Output:** List of all categories, including system and custom types.

- **POST /categories/update**

  - **Input:** `{ category_id: str, label: str, emoji?: str }`
  - **Output:** Updated category object.

- **POST /categories/apply**
  - **Input:** `{ transaction_ids: [str], category_id: str }`
  - **Output:** `{ success: boolean, updated: int }`

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

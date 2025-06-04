# backend/app/routes Documentation

---

## 📘 `accounts.py`

```markdown
# Accounts Route

## Purpose

Handles user account lifecycle operations, primarily focused on financial institution linking, management, and metadata sync. Integrates with external APIs (Plaid, Teller) and internal services for authentication and data ingestion.

## Key Endpoints

- `GET /accounts`: Retrieve all user-linked accounts.
- `POST /accounts/link`: Initiates link flow (typically with an external aggregator like Plaid).
- `DELETE /accounts/<account_id>`: Removes a linked account.
- `PATCH /accounts/<account_id>`: Updates account metadata (e.g., custom labels).

## Inputs & Outputs

- **POST /accounts/link**

  - **Input:** `{ public_token: str, provider: 'plaid' | 'teller' }`
  - **Output:** `{ account_id: str, status: str }`

- **GET /accounts**
  - **Output:** List of accounts with metadata (balance, institution name, link status)

## Internal Dependencies

- `services.account_link_service`
- `models.Account`
- Auth middleware for user scoping

## Known Behaviors

- Supports multi-provider account linkage
- Triggers metadata sync jobs on link success
- Enforces ownership validation on all mutations

## Related Docs

- [`docs/backend/services/account_link_service.md`](../services/account_link_service.md)
- [`docs/dataflow/sync_pipeline.md`](../../dataflow/sync_pipeline.md)
```

---

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

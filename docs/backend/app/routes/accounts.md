# Accounts and Categories Routes (`accounts.py`, `categories.py`)

## Accounts Route

### Purpose

Manages account lifecycle operations including institution linking, metadata updates, and removal of linked accounts with Plaid integration.

### Endpoints

- `GET /accounts` – Retrieve all linked accounts and metadata.
- `POST /accounts/link` – Initiate account linking via external aggregators such as Plaid.
- `PATCH /accounts/<account_id>` – Update stored account metadata.
- `DELETE /accounts/<account_id>` – Remove a linked account.
- `GET /accounts/<account_id>/net_changes` – Compute income, expense, and net movement between two dates.

### Inputs/Outputs

- **POST /accounts/link**
  - **Inputs:** JSON `{ "public_token": str, "provider": "plaid" }`.
  - **Outputs:** `{ "account_id": str, "status": str }` describing the new linkage.
- **GET /accounts**
  - **Outputs:** Array of linked accounts with balances, institution names, and link status metadata.
- **GET /accounts/<account_id>/net_changes**
  - **Inputs:** `start_date` and `end_date` query params to bound the range.
  - **Outputs:** `{ "status": "success", "data": { "income", "expense", "net" } }` plus legacy fields `{account_id, net_change, period: {start, end}}` for backward compatibility.

### Auth

- Requires authenticated user context; uses the standard auth middleware to scope linked accounts.

### Dependencies

- `services.account_link_service` for Plaid token exchange and account provisioning.
- `models.Account` for persistence.

### Behaviors/Edge Cases

- Triggers metadata sync jobs when a link succeeds.
- Validates token payloads before invoking Plaid.
- Deletions cascade to associated metadata according to model constraints.
- Net change calculations rely on balance snapshots in `AccountHistory` and fall back to transaction aggregation when snapshots are incomplete; ensure balance-history backfills are healthy to avoid gaps.

### Net Changes Logic

- `account_logic.get_net_change` retrieves `AccountHistory` snapshots for the provided `start_date` and `end_date` and returns `end_balance - start_balance` as the primary net change.
- The response envelope includes both the modern breakdown `{income, expense, net}` and the legacy top-level fields `{account_id, net_change, period:{start,end}}` to keep older consumers functional.
- When snapshots are missing, legacy `net_change` is derived from available history and transaction aggregation keeps the breakdown accurate.

### Sample Request/Response

```http
POST /accounts/link HTTP/1.1
Content-Type: application/json

{ "public_token": "public-sandbox-123", "provider": "plaid" }
```

```json
{ "account_id": "acc_123", "status": "linked" }
```

## Categories Route

### Purpose

Supports automatic and manual transaction categorization, including updates to category metadata and application of rules.

### Endpoints

- `GET /categories` – Fetch default and user-defined categories.
- `GET /categories/tree` – Provide nested category and detail relationships.
- `POST /categories/update` – Update category metadata (label, emoji, etc.).
- `POST /categories/apply` – Reassign category tags to transactions.
- `GET /rules` – List saved transaction rules.
- `POST /rules` – Create a new rule.
- `PATCH /rules/<id>` – Modify or disable a rule.
- `DELETE /rules/<id>` – Remove a rule.

### Inputs/Outputs

- **GET /categories**
  - **Outputs:** Full list of system and custom categories.
- **GET /categories/tree**
  - **Outputs:** Tree payload `{ "status": "success", "data": [{ "name": str, "children": [{ "id": int, "name": str }] }] }` for dropdowns.
- **POST /categories/update**
  - **Inputs:** `{ "category_id": str, "label": str, "emoji"?: str }`.
  - **Outputs:** Updated category object.
- **POST /categories/apply**
  - **Inputs:** `{ "transaction_ids": [str], "category_id": str }`.
  - **Outputs:** `{ "success": boolean, "updated": int }` summarizing updates.
- **GET /rules` / **POST /rules** / **PATCH /rules/<id>** / **DELETE /rules/<id>\*\*
  - **Inputs:** Rule criteria or partial updates depending on verb.
  - **Outputs:** Saved rule objects or `{ "success": boolean }` after deletion.

### Auth

- Requires authenticated user context; category lists and rules are scoped per user or institution.

### Dependencies

- `models.Category` for category persistence.
- `services.categorization_service` and related validation utilities for applying and updating categories.

### Behaviors/Edge Cases

- Automatic category assignment follows merchant rules but manual overrides persist across syncs.
- Enforces duplicate-label protection.
- Rule edits can deactivate logic without deletion.

### Sample Request/Response

```http
POST /categories/apply HTTP/1.1
Content-Type: application/json

{ "transaction_ids": ["txn_1", "txn_2"], "category_id": "cat_groceries" }
```

```json
{ "success": true, "updated": 2 }
```

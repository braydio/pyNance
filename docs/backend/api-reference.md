# API Reference - Routing and Service Conventions [API_REFERENCE]

This document serves as the authoritative reference for API routing conventions, service organization, and endpoint definitions in the pyNance application. All backend and frontend teams should refer to this for new route definitions, refactors, or frontend integrations.

> **Status:** Master Reference - All API changes must align with these conventions

## Live API Documentation

Run the backend server and navigate to `/api/docs` for the interactive Swagger UI or to `/api/docs.json` for the raw OpenAPI schema.
These live docs reflect the current application state, providing a quick way to verify request/response shapes alongside this
static markdown reference.

## Route Organization Structure [ROUTE_ORGANIZATION]

### 📁 `routes/` Directory Structure

| Module File             | Responsibility                                          |
| ----------------------- | ------------------------------------------------------- |
| `transactions.py`       | Shared transaction operations (paginated views, search) |
| `plaid_transactions.py` | Plaid-specific account + transaction routes             |
| `goals.py`              | Manage user-defined financial goals                     |
| `accounts.py`           | Account refresh, history, and transaction helpers       |

## 🌐 API Endpoint Convention

### 🔸 Shared Resources

```
GET    /api/transactions/get_transactions
PUT    /api/transactions/update
POST   /api/transactions/scan-internal
GET    /api/accounts/get_accounts
POST   /api/accounts/refresh_accounts
GET    /api/accounts/<id>/history
GET    /api/institutions
POST   /api/institutions/<id>/refresh
GET    /api/goals
POST   /api/goals
```

## 🧭 Planning & Allocation Endpoints

```text
GET    /api/planning/bills
POST   /api/planning/bills
PUT    /api/planning/bills/<bill_id>
DELETE /api/planning/bills/<bill_id>
GET    /api/planning/allocations
PUT    /api/planning/allocations
GET    /api/planning/scenarios/<scenario_id>/allocations
PUT    /api/planning/scenarios/<scenario_id>/allocations
```

**PUT /api/planning/scenarios/<scenario_id>/allocations**

Replaces the full allocation array for a planning scenario. When the frontend operates in API mode, `usePlanning.persistScenarioAllocations` issues this request after applying an optimistic update.

**Request body**

```json
[
  {
    "id": "alloc-uuid",
    "target": "savings:emergency",
    "kind": "percent",
    "value": 40
  }
]
```

**Response body**

```json
[
  {
    "id": "alloc-uuid",
    "target": "savings:emergency",
    "kind": "percent",
    "value": 40
  }
]
```

Clients should treat the response as the canonical allocation list—merge it back into local state to capture server-side adjustments or generated identifiers.

**GET /api/institutions**

Returns a list of institutions with their linked accounts and the most recent refresh timestamp.

**POST /api/institutions/<id>/refresh**

Refreshes all accounts under the specified institution. Accepts the same optional `start_date` and `end_date` parameters as `/api/accounts/refresh_accounts`.

**POST /api/accounts/refresh_accounts**

Optional JSON body parameters:

- `account_ids` – optional list of account IDs to refresh
- `start_date` – optional ISO `YYYY-MM-DD` start date
- `end_date` – optional ISO `YYYY-MM-DD` end date

Response body on success:

```json
{
  "status": "success",
  "updated_accounts": ["name"],
  "refreshed_counts": { "Bank A": 2 }
}
```

**GET /api/accounts/<id>/history**

Returns daily balances for the specified account. The `<id>` segment accepts
either the external `account_id` or the numeric primary key. An optional `range`
query parameter such as `7d`, `30d`, `90d`, or `365d` limits how many days are
returned.

**Query Parameters**

- `range` – number of days of history to return (default: `30d`)

**Response Body**

````json
{
  "accountId": "uuid",
  "asOfDate": "YYYY-MM-DD",
  "balances": [{ "date": "YYYY-MM-DD", "balance": 1523.21 }]
}

**GET /api/accounts/<account_id>/net_changes**

Returns income, expense, and net balance change for the specified account over a date range.

Query Parameters

- `start_date` – ISO `YYYY-MM-DD` start date (required)
- `end_date` – ISO `YYYY-MM-DD` end date (required)

Response Body

```json
{
  "status": "success",
  "data": { "income": 1250.0, "expense": 980.5, "net": 269.5 },
  "account_id": "uuid",
  "net_change": 269.5,
  "period": { "start": "YYYY-MM-DD", "end": "YYYY-MM-DD" }
}
````

Notes:

- `income` and `expense` are magnitudes; `net = income - expense`.
- Legacy fields (`account_id`, `net_change`, `period`) are preserved for backward compatibility.

````

**GET /api/accounts/<account_id>/transaction_history**

Returns a paginated list of transactions for the specified account. The `<account_id>` segment accepts either the external `account_id` or the numeric primary key. Excludes internal transactions by default.

**Query Parameters**

- `start_date` – optional ISO `YYYY-MM-DD` start date filter
- `end_date` – optional ISO `YYYY-MM-DD` end date filter
- `limit` – maximum number of transactions to return (default: 100, max: 1000)
- `offset` – number of transactions to skip for pagination (default: 0)
- `order` – sort order, `desc` (newest first) or `asc` (oldest first) (default: `desc`)
- `include_internal` – whether to include internal transactions (default: `false`)

**Response Body**

```json
{
  "status": "success",
  "account_id": "uuid",
  "transactions": [
    {
      "id": 123,
      "account_id": "uuid",
      "date": "YYYY-MM-DD",
      "description": "Transaction description",
      "amount": -45.67,
      "category": "Food and Drink",
      "is_internal": false
    }
  ],
  "paging": {
    "limit": 100,
    "offset": 0,
    "total_count": 250,
    "has_more": true,
    "next_offset": 100
  }
}
````

**PUT /api/transactions/update**

Updates persisted transaction metadata and flags without altering provider identifiers.

**Request Body**

- `transaction_id` (string, required) — target transaction identifier.
- Optional editable fields: `amount`, `date`, `description`, `category`, `merchant_name`, `merchant_type`, `is_internal`.
- Internal transfer helpers: `counterpart_transaction_id` to link pairs and `flag_counterpart` to mirror internal flags to the counterpart.
- Rule authoring controls (optional): set `save_as_rule: true` plus `rule_field`, `rule_value`, optional `rule_description`, and `rule_account_id` to persist a reusable categorisation rule.

**Responses**

- `200` with `{ "status": "success" }` on success.
- `400` for validation errors (missing ID, invalid amount/date), `404` when the transaction does not exist, `500` on unexpected failures.
- Legacy compatibility route `/api/transactions/user_modify/update` retains the same contract for older clients.

**POST /api/transactions/scan-internal**

Detects potential internal transfer pairs across transactions. The
endpoint returns candidate matches but does not modify any transaction flags.

**Response Body**

```json
{
  "status": "success",
  "pairs": [
    {
      "transaction_id": "T1",
      "counterpart_id": "T2",
      "amount": -100.0,
      "date": "2024-01-01",
      "description": "Transfer to savings",
      "counterpart": {
        "transaction_id": "T2",
        "amount": 100.0,
        "date": "2024-01-01",
        "description": "Transfer from checking"
      }
    }
  ]
}
```

### 🔹 Provider-Specific Resources

```
POST   /api/plaid/transactions/exchange_public_token
POST   /api/plaid/transactions/refresh_accounts
POST   /api/plaid/transactions/sync
POST   /api/plaid/transactions/generate_update_link_token
DELETE /api/plaid/transactions/delete_account
```

**POST /api/plaid/transactions/refresh_accounts**

Optional JSON body parameters:

- `start_date` – optional ISO `YYYY-MM-DD` start date
- `end_date` – optional ISO `YYYY-MM-DD` end date
- `account_ids` – optional list of account IDs to refresh

**POST /api/plaid/transactions/generate_update_link_token**

Generates a Plaid Link token in "update mode" for re-authenticating an account when credentials must be updated (typically for ITEM_LOGIN_REQUIRED errors).

**Required JSON body parameters:**

- `account_id` – Account identifier (accepts either numeric primary key or external account_id)

**Response body on success:**

```json
{
  "status": "success",
  "link_token": "link-sandbox-abc123...",
  "expiration": "2025-08-23T21:00:00Z",
  "account_id": "uuid"
}
```

**Error responses:**

- `400` – Missing `account_id` parameter
- `404` – Account not found
- `502` – Plaid API error

**Rule:**

- Generic paths: shared or abstracted logic
- `/plaid/`: must only contain Plaid provider logic

---

## 📦 Frontend Service Structure (Vue 3)

| File                    | Purpose                         |
| ----------------------- | ------------------------------- |
| `plaidService.js`       | Handles Plaid API interactions  |
| `transactionService.js` | Handles shared transaction APIs |
| `accountService.js`     | Shared accounts (get/delete)    |

Each service should:

- Contain only network + DTO logic (not sorting or filters)
- Match its route namespace (1-to-1 where possible)

---

## 🏷️ Naming Conventions

| Entity      | Convention     |
| ----------- | -------------- |
| Endpoint    | snake_case     |
| Route group | singular nouns |
| Table/model | PascalCase     |
| Service fn  | camelCase      |

Examples:

- `get_transactions`, `delete_account`
- `PlaidAccount`, `Transaction`
- `refreshAccounts()`, `exchangePublicToken()`

---

## 📍 Notes for Migration

- If a shared route grows provider-specific logic, extract it to a new provider file
- Backwards compatibility should be preserved when renaming public endpoints
- Any changes to `/api/transactions/get_transactions` must notify frontend
- ✅ These conventions **must be enforced via linting or pre-commit checks** to ensure consistency

## ✅ Canonical Endpoint Designation

The following route is the **canonical** source of paginated transaction data for all frontend views:

```text
GET /api/transactions/get_transactions
```

**Query Parameters**

- `start_date` – optional ISO `YYYY-MM-DD` start date
- `end_date` – optional ISO `YYYY-MM-DD` end date
- `category` – optional transaction category filter

This endpoint:

- Serves a unified view of transaction data across all providers
- Returns a JSON body with the transaction list and a `total` count
- Is consumed by dashboard components and paginated tables
- Must remain stable in shape and behavior to prevent frontend regressions

> Provider-specific filtering (e.g., only Plaid accounts) should be handled via query params or within the shared SQL layer—not by introducing new parallel routes.

---

**Last Updated:** 2025-06-12

Tag: `MASTER_API_REFERENCE`

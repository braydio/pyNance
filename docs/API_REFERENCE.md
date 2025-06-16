# API Routing and Service Convention Guide (Master Reference)

> **Status:** Authoritative. All backend and frontend teams should refer to this for new route definitions, refactors, or frontend integrations.

---

## 🗂️ Route Organization Structure

### 📁 `routes/` Directory Structure

| Module File              | Responsibility                                          |
| ------------------------ | ------------------------------------------------------- |
| `transactions.py`        | Shared transaction operations (paginated views, search) |
| `plaid_transactions.py`  | Plaid-specific account + transaction routes             |
| `teller_transactions.py` | Teller-specific account + transaction routes            |
| `accounts.py` (future)   | Shared account listings & deletion                      |

## 🌐 API Endpoint Convention

### 🔸 Shared Resources

```
GET    /api/transactions/get_transactions
GET    /api/accounts/get_accounts
POST   /api/accounts/refresh_accounts
GET    /api/institutions
POST   /api/institutions/<id>/refresh
```

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
{ "status": "success", "updated_accounts": ["name"], "refreshed_counts": { "Bank A": 2 } }
```

### 🔹 Provider-Specific Resources

```
POST   /api/plaid/transactions/exchange_public_token
POST   /api/plaid/transactions/refresh_accounts
DELETE /api/plaid/transactions/delete_account
POST   /api/teller/transactions/sync
DELETE /api/teller/transactions/delete_account
```

**POST /api/plaid/transactions/refresh_accounts**

Optional JSON body parameters:

- `user_id` – ID of the user whose accounts should refresh
- `start_date` – optional ISO `YYYY-MM-DD` start date
- `end_date` – optional ISO `YYYY-MM-DD` end date
- `account_ids` – optional list of account IDs to refresh

**Rule:**

- Generic paths: shared or abstracted logic
- `/plaid/`, `/teller/`: must only contain that provider's logic

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

- `start_date` – optional ISO ``YYYY-MM-DD`` start date
- `end_date` – optional ISO ``YYYY-MM-DD`` end date
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

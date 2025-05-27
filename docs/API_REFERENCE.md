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
DELETE /api/accounts/delete_account
```

### 🔹 Provider-Specific Resources

```
POST   /api/plaid/transactions/exchange_public_token
POST   /api/plaid/transactions/refresh_accounts
POST   /api/teller/transactions/sync
```

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

---

**Last Updated:** 2025-05-25

Tag: `MASTER_API_REFERENCE`

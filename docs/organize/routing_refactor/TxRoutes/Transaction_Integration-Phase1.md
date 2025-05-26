### New/Updated Files

| File                                         | Role                                                          |
| -------------------------------------------- | ------------------------------------------------------------- |
| `backend/app/routes/product_transactions.py` | Thin route layer, accepts `/transactions/sync` requests       |
| `backend/app/services/transactions.py`       | Orchestration logic; receives request, dispatches to provider |
| `backend/app/providers/plaid.py`             | Implementation for Plaid logic                                |
| `backend/app/providers/teller.py`            | Implementation for Teller logic                               |
| `__init__.py` (core)                         | Aggregates new route for API usage                            |

### Existing Files to Phase Out (non-destructive during migration)

| File                     | Reason                                                |
| ------------------------ | ----------------------------------------------------- |
| `plaid_transactions.py`  | Redundant after routing abstraction                   |
| `teller_transactions.py` | Same logic to be handled via service + provider layer |

---

## 🧩 Component Responsibilities

### `product_transactions.py`

- Receives `/transactions/sync` request
- Validates payload: `provider`, `account_id`
- Passes to service layer

### `services/transactions.py`

- Receives request and uses `provider` as a routing key
- May apply shared logic (caching, enrichment, error wrapping)
- Dispatches to `providers/{provider}.py`

### `providers/plaid.py` & `providers/teller.py`

- Contain raw API integration for sync
- Return normalized data objects or error dictionaries

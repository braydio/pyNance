### New/Updated Files

| File                                         | Role                                                          |
| -------------------------------------------- | ------------------------------------------------------------- |
| `backend/app/routes/product_transactions.py` | Thin route layer, accepts `/transactions/sync` requests       |
| `backend/app/services/transactions.py`       | Orchestration logic; receives request, dispatches to provider |
| `backend/app/providers/plaid.py`             | Implementation for Plaid logic                                |
| `__init__.py` (core)                         | Aggregates new route for API usage                            |

### Existing Files to Phase Out (non-destructive during migration)

| File                    | Reason                              |
| ----------------------- | ----------------------------------- |
| `plaid_transactions.py` | Redundant after routing abstraction |

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

### `providers/plaid.py`

- Contains raw API integration for sync
- Returns normalized data objects or error dictionaries

---

## 🚧 Execution Plan (Expanded)

### Phase 1 – Bootstrapping

:

- [x] Create `routes/product_transactions.py`
  - ✅ Confirmed: Exists as new file alongside `transactions.py`

- [ ] Create `services/transactions.py`
  - 🔍 Not present in current `services/`; will be new

- [ ] Stub methods in `providers/plaid.py`
  - 🔍 `plaid_transactions.py` exists with inline logic
  - 🔍 `providers/` folder does not currently exist, will need creation

- [ ] Register router in `__init__.py`
  - 🔍 `backend/app/__init__.py` exists and includes `include_router(...)` logic

### Phase 2 – Integration

- [ ] Validate frontend can call `/transactions/sync`
  - 🔍 Frontend routes and clients unknown; requires simulation or frontend alignment

- [ ] Migrate logic from `plaid_transactions.py`
  - 🔍 Logic includes full transaction sync flow and error handling

- [ ] Apply shared middleware (auth, logging, validation)
  - 🔍 Existing route files use inline error handling; no global middleware layer currently observed

### Phase 3 – Cleanup

- [ ] Mark `plaid_transactions.py` as deprecated
  - 🔍 Located in `backend/app/routes`; contains tightly-coupled logic

- [ ] Update `docs/maintenance/deprecated/backend-routing-plan.md`
  - ✅ File exists with accurate format

- [ ] Add tests or sandbox payload checks
  - 🔍 Test coverage not reviewed yet; assumed to be handled manually or externally

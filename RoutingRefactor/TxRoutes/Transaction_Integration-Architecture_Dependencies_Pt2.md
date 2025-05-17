<!--toc:start-->

- [New/Updated Files](#newupdated-files)
- [Existing Files to Phase Out (non-destructive during migration)](#existing-files-to-phase-out-non-destructive-during-migration)
- [🧩 Component Responsibilities](#🧩-component-responsibilities)
  - [`product_transactions.py`](#producttransactionspy)
  - [`services/transactions.py`](#servicestransactionspy)
  - [`providers/plaid.py` & `providers/teller.py`](#providersplaidpy-providerstellerpy)
- [🚧 Execution Plan (Expanded)](#🚧-execution-plan-expanded)
  - [Phase 1 – Bootstrapping](#phase-1-bootstrapping)
  - [Phase 2 – Integration](#phase-2-integration)
  - [Phase 3 – Cleanup](#phase-3-cleanup)
  <!--toc:end-->

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

---

## 🚧 Execution Plan (Expanded)

### Phase 1 – Bootstrapping

- [x] Create `routes/product_transactions.py`

  - ✅ Confirmed: Exists as new file alongside `transactions.py`

- [ ] Create `services/transactions.py`

  - 🔍 Not present in current `services/`; will be new

- [ ] Stub methods in `providers/plaid.py`, `providers/teller.py`

  - 🔍 `plaid_transactions.py`, `teller_transactions.py` exist with inline logic
  - 🔍 `providers/` folder does not currently exist, will need creation

- [ ] Register router in `__init__.py`

  - 🔍 `backend/app/__init__.py` exists and includes `include_router(...)` logic

### Phase 2 – Integration

- [ ] Validate frontend can call `/transactions/sync`

  - 🔍 Frontend routes and clients unknown; requires simulation or frontend alignment

- [ ] Migrate logic from `plaid_transactions.py` and `teller_transactions.py`

  - 🔍 Logic includes full transaction sync flow and error handling

- [ ] Apply shared middleware (auth, logging, validation)

  - 🔍 Existing route files use inline error handling; no global middleware layer currently observed

### Phase 3 – Cleanup

- [ ] Mark `plaid_transactions.py`, `teller_transactions.py` as deprecated

  - 🔍 Located in `backend/app/routes`; contain tightly-coupled logic

- [ ] Update `docs/backend_routing_plan.md`

  - ✅ File exists with accurate format

- [ ] Add tests or sandbox payload checks

  - 🔍 Test coverage not reviewed yet; assumed to be handled manually or externally

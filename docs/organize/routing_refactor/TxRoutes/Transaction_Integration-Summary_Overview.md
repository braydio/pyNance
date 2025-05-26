# 📘 Integration Plan: Product-Level Transactions Routing

## 📌 Statement of Intent

This document defines the full implementation plan for integrating **product-level routing and logic abstraction for transactions** into the `pyNance` backend.

The requested feature aims to modularize transaction handling by separating product logic (e.g. "transactions") from provider logic (e.g. "Plaid", "Teller"). This will:

- Improve clarity in backend routing.
- Enable provider-agnostic orchestration.
- Support more consistent and scalable integration of additional financial providers.

### ✅ Definition of Done

This initiative is complete when:

1. Product-level routes are in place and callable (e.g. `/transactions/sync`).
2. Each route defers to a service layer that coordinates logic.
3. The service layer dispatches to one or more provider implementations.
4. Documentation is present in `docs/backend_routing_plan.md`.
5. Existing provider-specific route files are deprecated and replaced cleanly.

---

## 📂 File and Directory Targets

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

## 🚧 Execution Stages

### Phase 1 – Bootstrapping

- [x] Create new route file: `product_transactions.py`
- [ ] Create `services/transactions.py`
- [ ] Populate with Plaid + Teller call routing
- [ ] Register route in `__init__.py`

### Phase 2 – Integration

- [ ] Verify frontend can use `/transactions/sync` as drop-in
- [ ] Begin migrating existing `plaid_*.py` and `teller_*.py` logic
- [ ] Add intermediate logging or auth validation (if needed)

### Phase 3 – Cleanup

- [ ] Deprecate old route files
- [ ] Update `docs/backend_routing_plan.md`
- [ ] Add test coverage and fallback handling

---

## 📎 Required Info / Dependencies

- ✅ Provider account IDs and expected input schemas (already used)
- ❓ Final structure of provider logic — are all methods `sync_transactions(account_id)`?
- ❓ Do we need caching or deduplication at the service layer?

---

## 📈 Metrics for Progress Tracking

- [ ] % of provider logic moved into `providers/*.py`
- [ ] % of routes transitioned to product abstraction
- [ ] Count of consumers (front-end, internal jobs) updated
- [ ] Validation logic consistency across products

---

## ✅ Summary

This plan replaces fragmented, provider-bound transaction routing with a modular, product-first architecture. It enables growth, reduces duplication, and prepares the backend for long-term integration of multi-provider financial ecosystems.

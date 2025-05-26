# 📘 Integration Plan: Plaid Investments Support (Product-Based Architecture)

## 📌 Summary & Statement of Intent

This plan documents the integration of **Plaid Investments** support within the `pyNance` backend, using the newly established **product-first routing architecture**. The objective is to handle investment data as a standalone domain, routed through product-specific logic, and abstracted from Plaid-specific implementation details.

This effort mirrors the structure outlined in the `Product Transactions Integration Plan` and is the second domain being migrated into the modular architecture.

---

## 🎯 Feature Request

Implement API and backend support for **Plaid's `/investments/holdings`** and `/investments/transactions` endpoints under a unified interface:

- Route: `POST /investments/sync`
- Input: `{ provider: "plaid", account_id: "..." }`
- Output: Normalized holdings and transaction data

---

## ✅ Definition of Done

- Product-level route `product_investments.py` exists and is functional
- Shared service logic exists at `services/investments.py`
- Plaid-specific implementation lives in `providers/plaid.py`
- Route is registered in `__init__.py`
- Manual and automated test pass for all sync paths
- Usage instructions are added to `backend_routing_plan.md`

---

## 🧱 Implementation Structure

### 1. Route Layer – `routes/product_investments.py`

- Accepts `POST /investments/sync`
- Validates: `provider`, `account_id`
- Passes to service layer

### 2. Service Layer – `services/investments.py`

- Receives input
- Switches based on provider
- Routes to `plaid.get_investments(account_id)`

### 3. Provider Layer – `providers/plaid.py`

- Adds function:

```python
 def get_investments(account_id: str):
     # Calls Plaid /investments/holdings and /transactions
     # Normalizes results and returns unified object
```

### 4. Registration – `app/__init__.py`

- `include_router(product_investments.router, prefix="")`

---

## 🚧 Execution Plan

### Phase 1 – Foundation

- [ ] Create `routes/product_investments.py`
- [ ] Create `services/investments.py`
- [ ] Add stub `get_investments` to `providers/plaid.py`

### Phase 2 – Feature Integration

- [ ] Call Plaid's `/investments/holdings` and `/transactions`
- [ ] Normalize and merge result objects
- [ ] Handle errors and timeouts
- [ ] Return standardized payload to service layer

### Phase 3 – System Integration

- [ ] Register route in `__init__.py`
- [ ] Add usage to docs
- [ ] Verify frontend compatibility or simulate requests
- [ ] Write test payloads with Plaid sandbox data

---

## 🧩 Design Notes

- The service layer can accommodate future providers (e.g. Alpaca, custom holdings CSV)
- Data normalization ensures internal clients don’t need to understand provider-specific quirks
- May later need a caching layer to handle large or slow responses from Plaid

---

## 📎 Requirements

- [x] Plaid account tokens + account_id access (existing from previous integrations)
- [ ] Response shape schema for investment holdings + transactions
- [ ] Clarification if investment sync should be merged with transaction sync

---

## 📈 Tracking Criteria

- [ ] Route defined and callable
- [ ] Service stub invoked and routing properly
- [ ] Provider logic responds with valid structure
- [ ] Docs updated, code tested

---

## ✅ Summary

This feature expands the backend's financial insight capabilities by adding investment support through Plaid, while adhering to a scalable and modular architecture. It will set the foundation for supporting multiple investment data sources under a single, provider-agnostic endpoint.

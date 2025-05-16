# 🧭 Backend Routing Refactor Plan

## 📌 Overview

This document outlines the proposed restructuring of backend route logic in the `pyNance` project to improve modularity, maintainability, and scalability. The key idea is to move away from provider-centric routing (e.g., `plaid_transactions.py`) toward a **product-first routing architecture** (e.g., `transactions.py` → `services/transactions.py` → `providers/plaid.py`).

---

## ✅ Goals

- Decouple routing logic from provider-specific implementations.
- Enable flexible switching or parallel use of providers.
- Encourage separation of concerns: routing, orchestration, and execution.
- Improve testability, traceability, and developer onboarding.

---

## 🔁 Proposed Flow

```
Frontend ➝ /transactions ➝ routes/transactions.py ➝ services/transactions.py ➝ providers/plaid.py | teller.py
```

### Breakdown

1. **Frontend specifies product-level intent** (e.g. sync transactions).
2. **Route module** dispatches to a shared service layer.
3. **Service module** handles business logic, validation, enrichment.
4. **Provider module** encapsulates communication with external APIs.

---

## 🧱 Example Structure

```
backend/app/
├── routes/
│   ├── transactions.py         # Thin route layer
│   └── plaid_transactions.py  # ❌ Will be deprecated
├── services/
│   └── transactions.py         # Shared business logic
├── providers/
│   ├── plaid.py                # Plaid-specific API integration
│   └── teller.py               # Teller-specific logic
```

---

## ⚠️ Problems in Current Architecture

- Routes are tightly coupled to provider (e.g. `plaid_transactions.py`).
- Shared logic is repeated or scattered.
- Services folder underutilized.
- No middleware tier to handle cross-cutting concerns (auth, logging, fallback).

---

## 🚧 Execution Process

1. **Introduce new route entrypoints** for major products: `transactions`, `investments`, `identity`, etc.
2. **Move orchestration logic** to `services/` files.
3. **Extract provider-specific code** into `providers/`.
4. **Gradually deprecate** old provider-specific route files.
5. **Update `__init__.py`** to register new product routes.

---

## 🧩 Potential Challenges

- Large surface area: 14–18 routes, 4–6 service domains.
- Test coverage may lag as logic is moved.
- Coordination with front-end for endpoint consistency.
- Temporary duplication during transition.

---

## 🗂 Suggested File Location

**Path:** `docs/backend_routing_refactor.md`

**Why:**

- Belongs in versioned documentation.
- Directly relevant to architectural decisions.
- Avoids cluttering implementation or tracking layers.
- Already consistent with `docs/backend_routing_plan.md`.

---

## ✅ Summary

This plan positions the backend to scale across providers without growing complexity. It supports domain ownership, cleaner testing, and better developer experience while allowing incremental adoption.

# backend_routing_plan.md

Blank routing plan for refactoring, enhancing, and aggregating routes in the PyNance backend.

This specifics way to standardize incoming and adding routes.

## Current Status

- Routes are all defined in `app/routes`/
- Product-specific routes are spread across files in a flat directory.
- No shared initializer or router accumulator is used.

- Plaid routes widely distributed:
  - `plaid.py`
  - `plaid_transactions.py`
  - `plaid_transfer.py`
  - `plaid_investments.py`
  - `plaidRouter.py` [candidate]

## Proposed Refactoring

- Create `app/routes/plaid`/ directory
  - Each file will correspond toa Plaid product
  - Naming convention: `plaid_{name}.py`(e.g. `plaid_auth.py`)

`/routes/plaid/auth.py
  /routes/plaid/transfer.py
  ...`

Example modules:

- `plaid_auth.py`
- `plaid_assets.py`
- `plaid_identity.py`
- `plaid_income.py`

## Router Aggregation

- plaid/route modules define `router = APIRouter()`
- initialized in `app/__core__.include.py` or app/**init**.py

example:

from app.routes.plaid import (plaid_auth, plaid_transfer, ...)

app.include_router(plaid_auth.router, prefix="/plaid")
app.include_router(plaid_transfer.router, prefix="/plaid")

## Notes

- Intent is focused on reducing route balling, enhancing testability, and make route responsibilities more explicit.
- Modularized file loading will enable much more clean-looking registration in ``**init**.py`.

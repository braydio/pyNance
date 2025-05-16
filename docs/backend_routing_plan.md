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

`
  /routes/plaid/auth.py
  /routes/plaid/transfer.py
  ...
`

Example modules:
- `plaid_auth.py`
- `plaid_assets.py`
- `plaid_identity.py`
- `plaid_income.py`

## Router Aggregation
- plaid/route modules define `router = APIRouter()`
- initialized in `app/__core__.include.py` or app/__init__.py

example:

  from app.routes.plaid import (plaid_auth, plaid_transfer, ...)

  app.include_router(plaid_auth.router, prefix="/plaid")
  app.include_router(plaid_transfer.router, prefix="/plaid")

## Notes
- Intent is focused on reducing route balling, enhancing testability, and make route responsibilities more explicit.
- Modularized file loading will enable much more clean-looking registration in ``__init__.py`.

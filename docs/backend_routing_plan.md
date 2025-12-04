# Backend routing plan status (deprecated)

## Assessment

- The project now exposes Flask blueprints under `backend/app/routes/` (for example, `transactions.py`, `plaid_investments.py`, `frontend.py`), which does not align with the FastAPI-style `APIRouter` approach described in the original plan.
- A services layer already exists (`backend/app/services/transactions.py`, `planning_service.py`, `sync_service.py`, etc.), but there is no `providers/` package. Introducing one would be a new architectural pattern not captured anywhere else in the codebase.
- Related planning notes live in `docs/routing_refactor_2025-05-16.md`, making this file a duplicated and partially contradictory source of truth.

## Decision

This document is deprecated. The architecture it proposes is incompatible with the current Flask blueprint setup and omits existing services that already handle orchestration. Continuing to evolve the routing strategy should happen in `docs/routing_refactor_2025-05-16.md` or a refreshed architecture note rather than here.

## Next steps

- Remove references to the old provider-first refactor and consolidate any future routing changes in a single, actively maintained document.
- If a provider abstraction is still desired, draft a new proposal that fits the current Flask stack and evaluate its impact on existing blueprints and services.

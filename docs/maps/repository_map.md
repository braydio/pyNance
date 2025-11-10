# Repository Map (2025-02-12)

This map captures the current state of the pyNance repository, highlighting active surfaces and legacy files that
should be archived or rewritten. Status levels:

- **Live** – used by the production stack or covered by tests.
- **Needs follow-up** – partially implemented or missing dependencies; audit soon.
- **Stale** – unused and safe to delete or move to `/archive`.

## Top-Level Summary

| Path | Status | Notes | Recommended action |
| --- | --- | --- | --- |
| `backend/` | Live | Flask API, CLI, and migrations registered via `backend/app/__init__.py`. | Continue routing/module consolidation; audit unregistered route files noted below. |
| `frontend/` | Live | Vue 3 app with views such as `Dashboard.vue`, `Accounts.vue`, and arbitrage screens. | Continue component cleanup and ensure docs match the current `src/` tree. |
| `arbit/` | Needs follow-up | Domain models/adapters exist, but the CLI expected by `arbit_cli.py` is missing. | Restore or decommission `arbit/cli.py`; otherwise update `ARBIT_CLI_PATH`. 【F:backend/app/services/arbit_cli.py†L1-L36】 |
| `scripts/` | Needs follow-up | Mix of active helpers (`setup.sh`, `dev-watcher.sh`) and ML/Chroma tooling. | Tag scripts by owner/purpose; remove unused automation after review. |
| `docs/` | Live | Comprehensive documentation tree across backend, frontend, process, and roadmaps. | Prune superseded reports during upcoming cleanup cycles. |
| `tests/` | Live | Pytest suite covering services, routes, and integrations. | Keep parity with new routes/services; expand coverage as features evolve. |
| `workers/` | Needs follow-up | Contains Plaid webhook worker used in some deployments. | Confirm deployment story or migrate logic into backend tasks. |
| `chromadb` | Stale | PostScript snapshot (`ImageMagick` export) with no runtime integration. | Archive or delete after confirming no one references the image. |
| `tools/` | Needs follow-up | One-off utilities (`symbol_map.py`). | Decide whether to fold into `scripts/` or document usage. |

## Backend Notes

- Application factory registers Flask blueprints in `backend/app/__init__.py`; any route not imported here is effectively
  dead code. 【F:backend/app/__init__.py†L14-L78】
- `backend/app/routes/` contains live blueprints (`accounts.py`, `plaid_transactions.py`, etc.) and several legacy modules
  that are never registered:
  - `product_transactions.py` is FastAPI-specific and unused. 【F:backend/app/routes/product_transactions.py†L1-L20】
  - `fidelity.py` references a missing `FidelityService`. 【F:backend/app/routes/fidelity.py†L1-L10】
  - `plaid_transfer.py` spins up an ad-hoc Flask app instead of a blueprint. 【F:backend/app/routes/plaid_transfer.py†L1-L60】
  - Recommend relocating these to an `/archive` folder or rewriting them as proper blueprints.
- Services under `backend/app/services/` are active, including arbitrage helpers and forecasting orchestration.
  Ensure future docs reference the SQL-backed services instead of old notebook workflows. 【F:backend/app/services/arbit_cli.py†L1-L36】
- Migrations in `backend/migrations/versions/` define canonical schema; keep `versions_archived/` for historical
  context but exclude from future autogeneration.

## Frontend Notes

- Vue application structure lives in `frontend/src/`, with views (`views/*.vue`) and shared components (`components/*.vue`).
  Key entry points include the arbitrage dashboards (`ArbitDashboard.vue`, `ArbitrageLive.vue`) that match backend routes.
  【F:frontend/src/views/ArbitDashboard.vue†L1-L30】【F:frontend/src/components/ArbitMetrics.vue†L1-L80】
- Legacy directory maps in `docs/maps/` were deleted because they referenced a pre-migration component tree. Maintain this
  document instead and update it when the frontend structure shifts.

## Scripts & Tooling

- Operational scripts (`scripts/setup.sh`, `scripts/dev-watcher.sh`) remain essential for onboarding and live reload
  workflows. 【F:scripts/dev-watcher.sh†L1-L80】
- Data/ML utilities such as `scripts/chroma_index.py` and `scripts/query_chroma.py` depend on optional services
  (ChromaDB) and should be reviewed for current value. 【F:scripts/chroma_index.py†L1-L70】
- Documentation aides (`scripts/check_docs.py`, `scripts/doc_cleaner.py`) help keep Markdown consistent—retain them and
  include in contributor onboarding. 【F:scripts/check_docs.py†L1-L120】

## Additional Observations

- `workers/plaid_webhook_worker.js` processes Plaid webhook events outside the Flask runtime; confirm whether deployments still
  rely on this worker or if Celery/Flask tasks supersede it. 【F:workers/plaid_webhook_worker.js†L1-L160】
- The root still contains a PostScript export at `chromadb`; no runtime references exist. Remove after capturing any needed
  visuals. 【F:chromadb†L1-L15】
- Tests frequently stub `app.sql` modules, which expect PostgreSQL at runtime but fall back to SQLite in unit tests. Keep this
  duality in mind when writing new cases. 【F:tests/test_api_transactions.py†L40-L50】

Update this map whenever major directories move or when stale modules are purged to keep future contributors oriented.

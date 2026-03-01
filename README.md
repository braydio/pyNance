# pyNance

[![Frontend CI](https://github.com/braydio/pyNance/actions/workflows/frontend-ci.yml/badge.svg)](https://github.com/braydio/pyNance/actions/workflows/frontend-ci.yml)

pyNance is a full-stack personal finance dashboard that combines a Flask API, a Vue 3 client, and a PostgreSQL database managed through SQLAlchemy and Alembic. It connects to financial institutions through Plaid to aggregate accounts and transactions.

## Features

- **Account aggregation and transactions** via Plaid integrations.
- **Rule-based categorization** to organize spending.
- **Balance forecasting** to project future account balances.
- **Forecast recompute API** (`POST /api/forecast/compute`) for scenario-based adjustments.
- **Goal tracking** for budgeting.
- **Investment tracking** alongside banking activity.
- **Deterministic account investment semantics** with persisted account-level flags (`is_investment`, holdings/transactions scope flags, and `account_type` normalization for API consumers).
- **Scenario planning** with planned bills and allocations (experimental).

## Sync & Webhooks

- Banking transactions use Plaid’s delta-based Transactions Sync with cursors.
  - Webhook: `POST /api/webhooks/plaid` listens for `TRANSACTIONS:SYNC_UPDATES_AVAILABLE` and triggers per‑account sync.
  - Manual: `POST /api/plaid/transactions/sync` exists for targeted refresh.
- Investments refresh automatically via Plaid webhooks:
  - `INVESTMENTS_TRANSACTIONS` → fetch recent investment transactions and upsert.
  - `HOLDINGS` → refresh holdings and securities.
- Raw payload storage: full Plaid objects are stored for audit/rehydration. See `docs/RAW_PAYLOAD_STORAGE.md`.

Webhook URL should point to `/api/webhooks/plaid`.

Pointing Plaid Webhooks

- New items (during Link): set `BACKEND_PUBLIC_URL` in `backend/.env` to your public backend URL. When using a Cloudflare Worker to proxy Plaid webhooks, set this to the worker's domain (e.g., `https://your-worker.example`). Link tokens will include `webhook = <BACKEND_PUBLIC_URL>/api/webhooks/plaid` automatically.
- After updating `BACKEND_PUBLIC_URL`, regenerate link tokens so Plaid registers the new webhook URL.
- Existing items: call the admin endpoint to update the webhook URL:
  ```bash
  curl -X POST \
    -H 'Content-Type: application/json' \
    -d '{"item_id":"<PLAID_ITEM_ID>"}' \
    <BACKEND_PUBLIC_URL>/api/plaid/webhook/update
  ```
  Or pass `{ "account_id": "<ACCOUNT_ID>" }` to resolve the item from an account.
  You can also override with `{ "webhook_url": "https://.../api/webhooks/plaid" }`.
  - Bulk update all items:
  ```bash
  curl -X POST \
    -H 'Content-Type: application/json' \
    -d '{}' \
    <BACKEND_PUBLIC_URL>/api/plaid/webhook/update_all
  ```

## Database Migrations

New JSON columns are used for raw payload storage. After pulling changes:

```bash
flask --app backend.run db migrate -m "add raw JSON cols for Plaid meta + investments"
flask --app backend.run db upgrade
```

## Quickstart (Flask + PostgreSQL)

1. **Install prerequisites:** [Docker + Docker Compose](https://docs.docker.com/compose/), [Python 3.12+](https://docs.python.org/3/), and [Node 20+](https://nodejs.org/en/docs/).
2. **Configure the backend:**

   ```bash
   cd backend
   bash scripts/setup.sh
   ```

   - Copies `backend/example.env` to `backend/.env`.
   - Spins up PostgreSQL via `backend/docker-compose.yml` and waits for readiness.
   - Applies Alembic migrations with `flask db upgrade` (see [Flask-Migrate](https://flask-migrate.readthedocs.io/en/latest/)).

3. **Run local services:**

   ```bash
   # Backend API (Flask)
   cd backend
   python run.py

   # Frontend (Vue 3)
   cd ../frontend
   npm install
   npm run dev
   ```

4. **Database utilities:**
   ```bash
   cd backend
   bash scripts/reset_db.sh   # drop/recreate + migrations
   bash scripts/seed_dev.sh   # load demo data
   ```

For auto-reloading during collaborative work, run the watcher from the project root:

```bash
./scripts/dev-watcher.sh
```

## Configuration

- `ENABLE_ARBIT_DASHBOARD` – set to `true` to enable the experimental arbitrage dashboard.

### Discord arbitrage feed

To surface live R/S arbitrage data in the UI, add the dashboard flag and run the Discord bot that publishes snapshots:

1. In `backend/.env` set `ENABLE_ARBIT_DASHBOARD=true`.
2. Run your Arbit Discord bot so it writes JSON updates to `backend/app/logs/rs_arbitrage.json`.
   The API reads this file and serves it at `/api/arbitrage/current`.
3. Start the backend and frontend, then visit `/arbitrage` in the browser to view the feed.

## Testing

- Backend tests:
  ```bash
  pytest
  ```
- Frontend component tests:
  ```bash
  cd frontend
  npm run test:unit
  ```

## Documentation

- Browse `docs/index/INDEX.md` for the structured documentation tree.
- Product roadmaps now live in `docs/roadmaps/`, keeping planning artifacts versioned with the codebase.
- Forecast response payloads and serialization models are documented in `docs/backend/forecast/models.md`.
- Forecast projection helpers are documented in `docs/backend/forecast/engine.md`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for coding standards and contribution guidelines.

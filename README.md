# pyNance

pyNance is a full-stack personal finance dashboard that combines a Flask API, a Vue 3 client, and a SQLite database. It connects to financial institutions through Plaid and Teller to aggregate accounts and transactions.

## Features

- **Account aggregation and transactions** via Plaid and Teller integrations.
- **Rule-based categorization** to organize spending.
- **Balance forecasting** to project future account balances.
- **Goal tracking** for budgeting.
- **Investment tracking** alongside banking activity.
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

- New items (during Link): set `BACKEND_PUBLIC_URL` in `backend/.env` to your public backend URL (e.g., `https://your-domain.example` or your tunnel URL). Link tokens will include `webhook = <BACKEND_PUBLIC_URL>/api/webhooks/plaid` automatically.
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

## Installation

```bash
./scripts/setup.sh
```

This script creates a virtual environment, installs backend and frontend dependencies, and copies `backend/example.env` to `backend/.env`.

## Running locally

1. Start the backend:
   ```bash
   cd backend
   flask --app app run
   ```
2. Start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

For automatic updates when new commits are pushed to the repository, use the
watcher script from the project root:

```bash
./scripts/dev-watcher.sh
```

It starts the frontend development server and periodically performs a
`git pull --rebase` when the tracked branch receives new commits, ensuring Git
hooks run and the server restarts with the latest changes.

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

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for coding standards and contribution guidelines.

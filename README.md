# pyNance

pyNance is a full-stack personal finance dashboard that combines a Flask API, a Vue 3 client, and a SQLite database. It connects to financial institutions through Plaid and Teller to aggregate accounts and transactions.

## Features

- **Account aggregation and transactions** via Plaid and Teller integrations.
- **Rule-based categorization** to organize spending.
- **Balance forecasting** to project future account balances.
- **Goal tracking** for budgeting.
- **Investment tracking** alongside banking activity.
- **Scenario planning** with planned bills and allocations (experimental).

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

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for coding standards and contribution guidelines.

# Environment & Configuration Reference

This guide centralizes all required and optional environment variables for running pyNance locally and in production.
It also provides verified examples and troubleshooting tips so you can get up and running quickly and safely.

## Quick Start

- Copy `backend/example.env` to `backend/.env` and fill in any blanks.
- Ensure `SQLALCHEMY_DATABASE_URI` points to your PostgreSQL instance.
- Apply migrations before running the API: `flask --app backend.run db upgrade`.
- Start services:
  - Backend: `flask --app backend.run run`
  - Frontend: `cd frontend && npm run dev`

## Backend Variables

- `SQLALCHEMY_DATABASE_URI` (required)
  - SQLAlchemy DSN for PostgreSQL. The API refuses to start without this.
  - Examples:
    - Local dev: `postgresql+psycopg://pynance:change-me@localhost:5432/pynance`
    - Managed: `postgresql+psycopg://USER:PASSWORD@HOST:PORT/DBNAME`
- `FLASK_ENV` (optional; default: `production`)
  - Common values: `development`, `production`.
- `CLIENT_NAME` (optional; default: `pyNance-Dash`)
  - Display name used in Plaid Link flows.

### Plaid

- `PLAID_CLIENT_ID` (required for Plaid features)
- `PLAID_SECRET_KEY` (required for Plaid features)
- `PLAID_ENV` (optional; default: `sandbox`)
  - One of `sandbox`, `development`, `production`.
- `PLAID_WEBHOOK_SECRET` (recommended)
  - Used to validate webhook signatures from Plaid.
- `PRODUCTS` (optional; default: `transactions`)
  - Comma‑separated list of Plaid products enabled for your app.

### Webhooks & Public URL

- `BACKEND_PUBLIC_URL` (recommended when using Plaid Link + webhooks)
  - Public base URL for your backend, used to register the webhook callback in Link tokens.
  - Example: `https://your-worker.example` or a tunnel URL like `https://abcd1234.ngrok.app`.
  - Webhook endpoint: `<BACKEND_PUBLIC_URL>/api/webhooks/plaid`
  - After changing this, regenerate Link tokens for existing users or call the admin endpoint to update items.

### Optional Feature Flags & Integrations

### Miscellaneous (Dev/Testing)

- `VARIABLE_ENV_TOKEN`, `VARIABLE_ENV_ID` (optional)
  - Utility tokens used in selective local workflows and tests.

## Frontend

The frontend typically does not require a `.env` for local development beyond Vite defaults. It expects the backend
to run on `http://localhost:5000` unless proxied. If you use a custom backend port or host, adjust the dev proxy in
`frontend/vite.config.*` accordingly.

## Migrations

- Initialise or upgrade schema:
  - `flask --app backend.run db upgrade`
- Create a new migration (when models change):
  - `flask --app backend.run db migrate -m "describe your change"`
  - `flask --app backend.run db upgrade`

## Verification

- Backend tests: `pytest -q`
- Lint and type checks: `pre-commit run --all-files`
- API sanity check: run the server and hit `/health` or core endpoints.

## Troubleshooting

- Error: `SQLALCHEMY_DATABASE_URI must be defined when running against PostgreSQL.`
  - Set `SQLALCHEMY_DATABASE_URI` in `backend/.env` to a valid PostgreSQL DSN.
- Error: `SQLALCHEMY_DATABASE_URI is not a valid SQLAlchemy URL.`
  - Verify scheme (`postgresql+psycopg://`), credentials, host, port, and database name.
- Plaid calls fail with auth errors
  - Ensure `PLAID_CLIENT_ID`, `PLAID_SECRET_KEY`, and `PLAID_ENV` are correct for your account.
- Webhook not firing or 400 on webhook endpoint
  - Confirm `BACKEND_PUBLIC_URL` is publicly reachable and the endpoint is `/api/webhooks/plaid`.
  - If validating signatures, set `PLAID_WEBHOOK_SECRET` to the value from your Plaid dashboard.

## Security

- Never commit secrets. Keep `.env` files local only.
- Rotate keys if exposed and consider read‑only users for local databases.

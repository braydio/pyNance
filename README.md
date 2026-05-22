# pyNance

[![Frontend CI](https://github.com/braydio/pyNance/actions/workflows/frontend-ci.yml/badge.svg)](https://github.com/braydio/pyNance/actions/workflows/frontend-ci.yml)

pyNance is a self-hosted full-stack personal finance platform built with Flask, Vue 3, PostgreSQL, SQLAlchemy, and Alembic. It integrates with Plaid to aggregate banking, transaction, and investment data while providing forecasting, categorization, planning, and analytics tooling.

> [!WARNING]
> pyNance is intended for self-hosted and development-oriented use. The application may expose sensitive financial data and includes experimental/admin functionality that should never be publicly exposed without proper authentication, network isolation, HTTPS, and security review. Do not deploy directly to the public internet without hardening the environment.

---

# Features

## Banking & Transactions

- Plaid-based account aggregation and transaction sync.
- Delta-based transaction synchronization using Plaid Transactions Sync cursors.
- Rule-based transaction categorization workflows.
- Manual transaction import and export tooling.
- Deterministic account classification and investment semantics.

## Forecasting & Planning

- Forward-looking balance forecasting.
- Forecast recompute API:
  - `POST /api/forecast/compute`
- Supports:
  - moving-average forecast windows
  - normalization toggles
  - graph modes
  - distributed manual adjustments
  - typed aspect-series overlays
  - debt and spending projections
  - wage-source metadata attribution

## Investments

- Investment account and holdings tracking.
- Plaid holdings + investment transaction refresh support.
- Persisted holdings, securities, and investment transaction history.

## UI & Frontend

- Vue 3 frontend with shared primitive components:
  - buttons
  - inputs
  - selects
  - chips
  - panels
- Consistent geometry, focus handling, and interaction behavior across high-traffic screens.

## Scenario Planning

Experimental financial planning features including:
- planned bills
- allocations
- budgeting goals
- forecasting scenarios

---

# Sync & Webhooks

## Transaction Sync

Plaid transaction ingestion uses delta-based synchronization with persistent cursors.

### Webhook Endpoint

```text
POST /api/webhooks/plaid
```

Handles:

```text
TRANSACTIONS:SYNC_UPDATES_AVAILABLE
```

and triggers targeted account refreshes.

### Manual Sync

```text
POST /api/plaid/transactions/sync
```

exists for targeted/manual refresh workflows.

## Investment Webhooks

Supported webhook events:

| Event | Behavior |
|---|---|
| `INVESTMENTS_TRANSACTIONS` | Refresh investment transactions |
| `HOLDINGS` | Refresh holdings and securities |

## Raw Payload Storage

Full Plaid payloads are persisted for:
- auditing
- reconciliation
- rehydration
- debugging

See:

```text
docs/RAW_PAYLOAD_STORAGE.md
```

---

# Plaid Webhook Configuration

Webhook URL:

```text
/api/webhooks/plaid
```

## New Plaid Items

Set:

```env
BACKEND_PUBLIC_URL=https://your-public-url
```

inside:

```text
backend/.env
```

When using a Cloudflare Worker or reverse proxy, point this variable to the externally accessible endpoint.

Generated Link tokens automatically include:

```text
<BACKEND_PUBLIC_URL>/api/webhooks/plaid
```

After updating `BACKEND_PUBLIC_URL`, regenerate Plaid Link tokens so Plaid registers the new webhook URL.

---

## Existing Plaid Items

Update webhook URLs manually:

```bash
curl -X POST \
  -H 'Content-Type: application/json' \
  -d '{"item_id":"<PLAID_ITEM_ID>"}' \
  <BACKEND_PUBLIC_URL>/api/plaid/webhook/update
```

You may also provide:

```json
{
  "account_id": "<ACCOUNT_ID>"
}
```

or override directly:

```json
{
  "webhook_url": "https://.../api/webhooks/plaid"
}
```

### Bulk Update

```bash
curl -X POST \
  -H 'Content-Type: application/json' \
  -d '{}' \
  <BACKEND_PUBLIC_URL>/api/plaid/webhook/update_all
```

---

# Database Migrations

After pulling schema changes:

```bash
flask --app backend.run db migrate -m "update schema"
flask --app backend.run db upgrade
```

---

# Quickstart

## Requirements

- Docker + Docker Compose
- Python 3.12+
- Node.js 20+

---

## Backend Setup

```bash
cd backend
bash scripts/setup.sh
```

This will:
- create `backend/.env`
- start PostgreSQL
- wait for readiness
- apply Alembic migrations

---

## Run Development Services

### Flask API

```bash
cd backend
python run.py
```

### Vue Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Database Utilities

```bash
cd backend

# Drop + recreate database
bash scripts/reset_db.sh

# Seed development/demo data
bash scripts/seed_dev.sh
```

---

## Dev Watcher

From the repository root:

```bash
./scripts/dev-watcher.sh
```

---

# Configuration

| Variable | Purpose |
|---|---|
| `ENABLE_ARBIT_DASHBOARD` | Enables experimental arbitrage dashboard |
| `OPENAI_API_KEY` | Optional LLM-generated dashboard activity summaries |

If no OpenAI key is configured, deterministic fallback messaging is used.

---

# Discord Arbitrage Feed

To expose live R/S arbitrage data:

1. Set:

```env
ENABLE_ARBIT_DASHBOARD=true
```

2. Run the Discord bot that writes snapshots to:

```text
backend/app/logs/rs_arbitrage.json
```

3. Access the dashboard at:

```text
/arbitrage
```

API endpoint:

```text
/api/arbitrage/current
```

---

# Testing

## Backend

```bash
pytest
```

## Frontend

```bash
cd frontend
npm run test:unit
```

---

# DeepSource

Static analysis configuration lives in:

```text
.deepsource.toml
```

Enabled analyzers:
- Python
- JavaScript (Vue)
- SQL

Coverage uploads are intentionally disabled until a dedicated pipeline is added.

Large/generated paths are excluded to reduce analysis overhead.

---

# Documentation

Primary documentation index:

```text
docs/index/INDEX.md
```

Additional references:
- `docs/roadmaps/`
- `docs/backend/forecast/models.md`
- `docs/backend/forecast/engine.md`

---

# Contributing

See:

```text
CONTRIBUTING.md
```

for contribution standards and development guidelines.

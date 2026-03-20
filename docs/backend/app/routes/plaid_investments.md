---
Owner: Backend Team
Last Updated: 2026-03-17
Status: Active
---

# Plaid Investments Route (`plaid_investments.py`)

## Purpose

Manage Plaid investments link setup and trigger investments data refresh workflows.

## Endpoints

- `POST /api/plaid/investments/generate_link_token`
- `POST /api/plaid/investments/exchange_public_token`
- `POST /api/plaid/investments/refresh`
- `POST /api/plaid/investments/refresh_all`

## Endpoint Contracts

### `POST /api/plaid/investments/generate_link_token`

Generate a Plaid Link token scoped to the `investments` product.

- Request JSON body:
  - `user_id` (required)
- Success response (`200`):

```json
{
  "status": "success",
  "link_token": "link-sandbox-..."
}
```

- Error responses:
  - `400` with `{ "error": "Missing user_id" }` when `user_id` is absent, request JSON is empty, JSON is malformed, or a non-object JSON payload is provided.
  - `500` with `{ "error": "..." }` for unexpected token-generation failures.

### `POST /api/plaid/investments/exchange_public_token`

Exchange a Plaid public token, persist linked accounts, and upsert Plaid item metadata.

- Request JSON body:
  - `user_id` (required)
  - `public_token` (required)
- Success response (`200`):

```json
{
  "status": "success",
  "item_id": "item_..."
}
```

- Error responses:
  - `400` with `{ "error": "Missing user_id or public_token" }` when required fields are absent, request JSON is empty, JSON is malformed, or a non-object JSON payload is provided.
  - `500` with `{ "error": "Failed to exchange public token" }` when Plaid exchange does not return `access_token`/`item_id`.
  - `500` with `{ "error": "..." }` for other unexpected exchange/sync failures.

Notes:

- The route upserts accounts via `upsert_accounts(...)`, stores Plaid account link rows with `save_plaid_account(...)`, and attempts to upsert a `PlaidItem` row.
- Product scopes for both `PlaidItem.product` and `PlaidAccount.product` are now canonicalized via `merge_plaid_products(...)` so linking investments after transactions preserves existing scopes and stores a deduplicated sorted value (for example, `investments,transactions`).
- Failure in the internal `PlaidItem` upsert block is logged but does not change the success response if the exchange itself succeeds.

### `POST /api/plaid/investments/refresh`

Refresh holdings/securities plus investment transactions for a specific linked Plaid investments item.

- Request JSON body:
  - `user_id` (required)
  - `item_id` (required)
  - `start_date` (optional, `YYYY-MM-DD`)
  - `end_date` (optional, `YYYY-MM-DD`)
- Date range behavior:
  - If either date is missing, both are defaulted to the last 30 days.
- Success response (`200`):

```json
{
  "status": "success",
  "upserts": {
    "securities": 10,
    "holdings": 24,
    "investment_transactions": 42
  }
}
```

- Error responses:
  - `400` with `{ "error": "Missing user_id or item_id" }` when required fields are absent, request JSON is empty, JSON is malformed, or a non-object JSON payload is provided.
  - `404` with `{ "error": "Investments account not found" }` when no `PlaidAccount` matches the provided `item_id` with a parsed product scope containing `investments` (supports canonical comma-delimited strings such as `"investments,transactions"`).
  - `500` with `{ "error": "..." }` for unexpected refresh failures.

### `POST /api/plaid/investments/refresh_all`

Refresh holdings/securities and transactions for all active Plaid accounts whose parsed scopes include the `investments` product.

- Request JSON body (optional):
  - `start_date` (optional, `YYYY-MM-DD`)
  - `end_date` (optional, `YYYY-MM-DD`)
- Date range behavior:
  - If either date is missing, both are defaulted to the last 30 days.
- Success response (`200`):

```json
{
  "status": "success",
  "summary": {
    "securities": 10,
    "holdings": 24,
    "investment_transactions": 42,
    "items": 3
  },
  "range": {
    "start_date": "2026-01-28",
    "end_date": "2026-02-27"
  }
}
```

- Error responses:
  - `500` with `{ "error": "..." }` for top-level failures.

Notes:

- Per-item refresh errors are logged and skipped (`continue`), so the route can still return `200` with partial aggregate results.

## Auth

- No route-level auth checks are implemented in this module.
- Access control, if required, must be enforced by upstream middleware, blueprint wrapping, or deployment boundary.

## Dependencies

- Plaid helper functions:
  - `generate_link_token`
  - `exchange_public_token`
  - `get_accounts`
  - `get_investment_transactions`
- Investments persistence helpers in `app.sql.investments_logic`.
- Account linkage helpers in `app.sql.account_logic`.
- Models: `PlaidAccount`, `PlaidItem`.

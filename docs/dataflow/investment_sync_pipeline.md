# Investment Sync Pipeline

This document describes the current end-to-end flow that syncs Plaid investment data into pyNance.

## 1) Link token + public token exchange (`plaid_investments.py`)

1. The frontend requests an investments link token via `POST /api/plaid/investments/generate_link_token`.
2. `generate_link_token_investments()` calls `generate_link_token(user_id, products=["investments"])`.
3. After Plaid Link returns a `public_token`, the frontend calls `POST /api/plaid/investments/exchange_public_token`.
4. `exchange_public_token_investments()` exchanges the token using `exchange_public_token(public_token)` and receives `access_token` + `item_id`.

## 2) Account + item persistence (`save_plaid_account`, `PlaidItem` upsert)

After token exchange succeeds, the route persists both account-level and item-level linkage:

1. It fetches Plaid accounts with `get_accounts(access_token, user_id)`.
2. It upserts core account rows with `upsert_accounts(...)`.
3. For each returned `account_id`, it calls `save_plaid_account(account_id, item_id, access_token, "investments")` to insert/update `PlaidAccount`.
4. It then upserts a single `PlaidItem` row keyed by `item_id` (update if exists, insert otherwise), storing the latest token and marking the row active.

This split keeps per-account linkage (`PlaidAccount`) and per-item token state (`PlaidItem`) in sync.

## 3) Holdings + securities ingest (`upsert_investment_holdings`)

The low-level holdings helper `investments_logic.upsert_investment_holdings(securities, holdings, commit=...)`:

1. Upserts each security into `Security` via `db.session.merge(...)`.
2. Upserts each holding into `InvestmentHolding` using PostgreSQL `ON CONFLICT` for `(account_id, security_id)`.
3. Optionally commits and returns summary counts (`securities`, `holdings`).

## 4) Investment transactions ingest (`get_investment_transactions` + `upsert_investment_transactions`)

Transaction refresh uses a two-step process:

1. Fetch from Plaid with `get_investment_transactions(access_token, start_date, end_date)`.
   - Accepts ISO date strings or `date`/`datetime` objects.
   - Coerces to Plaid-compatible dates.
   - Paginates with `count`/`offset` until all rows are retrieved.
2. Persist with `investments_logic.upsert_investment_transactions(txs, commit=...)`.
   - Upserts each row into `InvestmentTransaction` via `db.session.merge(...)`.
   - Optionally commits once per batch and returns the processed count.

## 4a) Atomic orchestration (`sync_investments_from_plaid`)

Refresh routes now prefer `investments_logic.sync_investments_from_plaid(user_id, access_token, start_date, end_date, commit=False)`, which:

1. Fetches holdings/securities from Plaid.
2. Persists securities and holdings without committing.
3. Fetches investment transactions for the requested window.
4. Persists transactions without committing.
5. Lets the caller issue one final commit so any failure rolls back the full investment refresh.

### Date-window behavior

- `POST /api/plaid/investments/refresh` accepts optional `start_date`/`end_date` in the request body.
- `POST /api/plaid/investments/refresh_all` also accepts optional `start_date`/`end_date`.
- If either endpoint is called without a complete window, both default to the last 30 days.

## 5) Webhook-driven incremental updates (`plaid_webhook.py`)

Plaid webhooks arrive at `POST /api/webhooks/plaid`. For investments:

1. `webhook_type == "INVESTMENTS_TRANSACTIONS"` with `webhook_code` in `DEFAULT_UPDATE`, `HISTORICAL_UPDATE`:
   - Finds all investment `PlaidAccount` rows for the `item_id`.
   - Fetches transactions for a safe rolling window (last 30 days).
   - Upserts via `upsert_investment_transactions(...)`.
2. `webhook_type == "HOLDINGS"` with `webhook_code == "DEFAULT_UPDATE"`:
   - Finds all investment `PlaidAccount` rows for the `item_id`.
   - Refreshes holdings/securities via `upsert_investments_from_plaid(...)`.

This means investments data can be updated both manually (refresh endpoints) and reactively (webhooks).

## Operational refresh entry points

Current investment refresh API entry points are:

- `POST /api/plaid/investments/refresh` for one linked investment item (`user_id` + `item_id`).
- `POST /api/plaid/investments/refresh_all` for all active linked investment items.

Both entry points execute holdings/securities ingest first, then transaction ingest for the selected date window, and commit only after the full item refresh succeeds.

# 📈 Plaid Investments Integration

This integration stores Plaid investment items and allows holdings to be refreshed.

## Database Table

`PlaidAccount` tracks each investment account:

- `account_id` – Plaid account identifier
- `item_id` – associated Plaid item
- `access_token` – token used for API calls
- `product` – `investments`
- `last_refreshed` – timestamp of last sync

## Refresh Flow

1. `/api/plaid/investments/generate_link_token` generates a Link token limited to the investments product.
2. `/api/plaid/investments/exchange_public_token` exchanges the public token and saves `PlaidAccount` rows via `save_plaid_account`.
3. `/api/plaid/investments/refresh` looks up the stored `PlaidAccount` and calls `get_investments`.

See [`docs/dataflow/investment_sync_pipeline.md`](../dataflow/investment_sync_pipeline.md) for the full sync pipeline.

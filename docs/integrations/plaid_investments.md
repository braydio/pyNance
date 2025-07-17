# 📈 Plaid Investments Integration

This integration stores Plaid investment items and allows holdings to be refreshed.

## Database Table

`PlaidItem` records each linked item:

- `user_id` – owner of the item
- `item_id` – unique Plaid item identifier
- `access_token` – token used for API calls
- `institution_name` – optional display name
- `product` – `investments`
- `last_refreshed` – timestamp of last sync

## Refresh Flow

1. `/api/plaid/investments/generate_link_token` generates a Link token limited to the investments product.
2. `/api/plaid/investments/exchange_public_token` exchanges the public token and saves a `PlaidItem` entry via `save_plaid_item`.
3. `/api/plaid/investments/refresh` looks up the stored `PlaidItem` and calls `get_investments`.

See [`docs/dataflow/investment_sync_pipeline.md`](../dataflow/investment_sync_pipeline.md) for the full sync pipeline.

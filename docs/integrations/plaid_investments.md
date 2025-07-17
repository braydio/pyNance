# 📈 Plaid Investments Integration

This page explains how investment accounts are linked through Plaid, how the item information is stored, and how holdings are refreshed.

## Linking Investment Items

1. The client requests `/plaid/investments/generate_link_token` with a `user_id`.
2. A Plaid link token scoped to the "investments" product is generated and returned.
3. After the user completes the Plaid Link flow, the frontend exchanges the returned `public_token` via `/plaid/investments/exchange_public_token`.
4. The backend stores the resulting access token and item metadata using `save_plaid_item`.

## Database Table: `plaid_items`

Investment link metadata is persisted in the `plaid_items` table via the `PlaidItem` model. Key fields include:

- `id` – primary key
- `user_id` – owning user
- `item_id` – Plaid item identifier
- `access_token` – token used for API calls
- `institution_name` – institution label
- `product` – Plaid product ("investments")
- `created_at` – record creation timestamp
- `updated_at` – timestamp of last update

## Refreshing Holdings

The `/plaid/investments/refresh` route accepts a `user_id` and `item_id`. It looks up the stored `PlaidItem`, retrieves current holdings via the Plaid API, and updates internal records.


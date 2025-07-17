# 💹 Investment Sync Pipeline

This document summarizes how investment data flows from Plaid into the database.

1. A user links an account via the `/api/plaid/investments/generate_link_token` and `/exchange_public_token` endpoints.
2. The exchanged token and item ID are stored in the `PlaidItem` table.
3. `/api/plaid/investments/refresh` retrieves holdings using `get_investments(access_token)`.
4. Holdings and securities can then be persisted or processed downstream (logic not yet implemented).

This pipeline mirrors the transaction refresh flow but is scoped specifically to Plaid's investments product.

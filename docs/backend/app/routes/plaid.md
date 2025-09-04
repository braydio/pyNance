# backend/app/routes Documentation

---

## 📘 `plaid.py`

````markdown
# Plaid Integration Route

## Purpose

Handles authentication and data integration with the Plaid API. Supports institution linking, token exchange, webhook verification, and data synchronization for accounts, transactions, and balances.

## Key Endpoints

- `POST /plaid/link-token`: Initiates link token generation. Accepts optional
  `products` array to enable multiple Plaid products in a single Link flow.
- `POST /plaid/exchange`: Exchanges public token for access token. Requires a
  `product` field to tag the resulting credentials.
- `GET /plaid/accounts`: Retrieves linked account metadata.
- `GET /plaid/transactions`: Fetches Plaid-synced transactions.
- `POST /plaid/sync`: Forces a manual sync with Plaid.

## Inputs & Outputs

- **POST /plaid/link-token**
  - **Input:** `{ user_id: str, products?: [str, ...] }`
  - **Output:** `{ link_token: str }`

- **POST /plaid/exchange**
  - **Input:** `{ public_token: str, product: str }`
  - **Output:** `{ access_token: str, item_id: str, product: str }`

- **GET /plaid/accounts**
  - **Output:**
    ```json
    [{ "id": "plaid_001", "name": "Checking", "balance": 820.34 }]
    ```

- **POST /plaid/sync**
  - **Input:** `{ access_token: str }`
  - **Output:** `{ transactions_synced: int, status: string }`

## Internal Dependencies

- `services.plaid_client`
- `models.Account`, `models.Transaction`
- Secrets manager for Plaid credentials

## Known Behaviors

- Uses client-side link flow for Plaid integration
- Triggers webhook registration post-link
- Syncs occur automatically and can be forced
- When multiple products are requested, Plaid generates a single link token
  covering each product. The client must call `/plaid/exchange` separately for
  every selected product so the backend can persist credentials with a
  product tag.

## Related Docs

- [`docs/dataflow/plaid_ingestion_pipeline.md`](../../dataflow/plaid_ingestion_pipeline.md)
- [`docs/integrations/plaid_config.md`](../../integrations/plaid_config.md)
````

---

Next: `plaid_investments.py`?

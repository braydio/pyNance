# backend/app/routes Documentation

---

## 📘 `plaid.py`

````markdown
# Plaid Integration Route

## Purpose

Handles authentication and data integration with the Plaid API. Supports institution linking, token exchange, webhook verification, and data synchronization for accounts, transactions, and balances.

## Key Endpoints

- `POST /plaid/link-token`: Initiates a link token generation.
- `POST /plaid/exchange`: Exchanges public token for access token.
- `GET /plaid/accounts`: Retrieves linked account metadata.
- `GET /plaid/transactions`: Fetches Plaid-synced transactions.
- `POST /plaid/sync`: Forces a manual sync with Plaid.

## Inputs & Outputs

- **POST /plaid/link-token**

  - **Input:** `{}`
  - **Output:** `{ link_token: str }`

- **POST /plaid/exchange**

  - **Input:** `{ public_token: str }`
  - **Output:** `{ access_token: str, item_id: str }`

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

## Related Docs

- [`docs/dataflow/plaid_ingestion_pipeline.md`](../../dataflow/plaid_ingestion_pipeline.md)
- [`docs/integrations/plaid_config.md`](../../integrations/plaid_config.md)
````

---

Next: `plaid_investments.py`?

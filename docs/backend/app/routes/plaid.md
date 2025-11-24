# Plaid Integration Route (`plaid.py`)

## Purpose
Handle Plaid link flows, token exchange, account retrieval, transaction syncs, and webhook verification for aggregated data ingestion.

## Endpoints
- `POST /plaid/link-token` – Generate a Link token, optionally enabling multiple Plaid products.
- `POST /plaid/exchange` – Exchange a public token for an access token tagged with the requested product.
- `GET /plaid/accounts` – Retrieve linked account metadata from Plaid.
- `GET /plaid/transactions` – Fetch Plaid-synced transactions.
- `POST /plaid/sync` – Force a manual Plaid sync.

## Inputs/Outputs
- **POST /plaid/link-token**
  - **Inputs:** `{ "user_id": str, "products"?: [str, ...] }`.
  - **Outputs:** `{ "link_token": str }`.
- **POST /plaid/exchange**
  - **Inputs:** `{ "public_token": str, "product": str }`.
  - **Outputs:** `{ "access_token": str, "item_id": str, "product": str }`.
- **GET /plaid/accounts**
  - **Inputs:** None.
  - **Outputs:** Array of account objects with balances and names.
- **POST /plaid/sync**
  - **Inputs:** `{ "access_token": str }`.
  - **Outputs:** `{ "transactions_synced": int, "status": str }`.

## Auth
- Uses authenticated user context; Plaid credentials are managed per user/institution.

## Dependencies
- `services.plaid_client` plus Plaid credential storage.
- `models.Account` and `models.Transaction` for persistence.

## Behaviors/Edge Cases
- When multiple products are requested, the client must exchange the token per product so credentials are tagged correctly.
- Syncs occur automatically but can be manually triggered when data staleness is detected.

## Sample Request/Response
```http
POST /plaid/exchange HTTP/1.1
Content-Type: application/json

{ "public_token": "public-sandbox-123", "product": "transactions" }
```

```json
{ "access_token": "access-sandbox-abc", "item_id": "item-123", "product": "transactions" }
```

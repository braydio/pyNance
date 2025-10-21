# Plaid Link Request Flow

This diagram traces how the Plaid Link onboarding request moves through the stack—from the Vue frontend initializer, into the Flask backend, out to Plaid, and back into the database before refreshed data is served to the UI.

```mermaid
sequenceDiagram
    participant Vue as Frontend<br/>`LinkProviderLauncher`
    participant ApiClient as Frontend API Client<br/>`accounts_link.js`
    participant Flask as Flask Backend<br/>`plaid_transactions`
    participant Helpers as Plaid Helper Layer<br/>`plaid_helpers`
    participant Plaid as Plaid API
    participant DB as Database
    participant Reader as Frontend Data Fetcher<br/>`services/api.js`

    %% Frontend initializes Plaid Link
    Vue->>ApiClient: POST /plaid/transactions/generate_link_token<br/>user_id, products
    ApiClient->>Flask: HTTP request (JSON payload)
    Flask->>Helpers: generate_link_token(user_id, products)
    Helpers->>Plaid: /link/token/create
    Plaid-->>Helpers: link_token
    Helpers-->>Flask: link_token
    Flask-->>ApiClient: {{ "link_token": token }}
    ApiClient-->>Vue: Provide link_token
    Vue->>Vue: window.Plaid.create(token)

    %% User completes Plaid Link, frontend exchanges token
    Vue->>ApiClient: POST /plaid/transactions/exchange_public_token<br/>public_token, user_id, products
    ApiClient->>Flask: HTTP request (JSON payload)
    Flask->>Helpers: exchange_public_token(public_token)
    Helpers->>Plaid: /item/public_token/exchange
    Plaid-->>Helpers: access_token, item_id
    Helpers-->>Flask: access_token, item_id
    Flask->>Helpers: get_item(access_token)
    Helpers->>Plaid: /item/get
    Plaid-->>Helpers: item metadata (institution_id)
    Helpers-->>Flask: item metadata
    Flask->>Helpers: get_accounts(access_token, user_id)
    Helpers->>Plaid: /accounts/get
    Plaid-->>Helpers: account list
    Helpers-->>Flask: account list

    %% Backend persistence layer
    Flask->>DB: Upsert PlaidItem & PlaidAccount rows
    Flask->>DB: account_logic.upsert_accounts(user_id, accounts, provider="plaid")
    DB-->>Flask: Commit persisted items & balances
    Flask-->>ApiClient: {{ "status": "success", "item_id": item_id }}
    ApiClient-->>Vue: notify success & emit("refresh")

    %% Frontend refreshes displayed data
    Vue->>Reader: emit refresh event
    Reader->>ApiClient: GET /accounts/get_accounts
    ApiClient->>Flask: HTTP request (query params)
    Flask->>DB: Query Account models & balances
    DB-->>Flask: Account rows with normalized balances
    Flask-->>ApiClient: {{ "accounts": [...] }}
    ApiClient-->>Reader: Return updated account payload
    Reader->>Vue: Update stores / UI with new accounts & balances
```

**Key touchpoints**

- **Frontend initializer**: `LinkProviderLauncher.vue` loads the Plaid script, requests a link token, and opens the Plaid Link modal. Upon success it calls `exchangePublicToken` and emits a refresh event back to parent components. 【F:frontend/src/components/forms/LinkProviderLauncher.vue†L1-L84】
- **Backend routes**: `/plaid/transactions/generate_link_token` and `/plaid/transactions/exchange_public_token` live in `plaid_transactions.py`, orchestrating Plaid helper calls, upserting `PlaidItem` / `PlaidAccount` records, and delegating to `account_logic.upsert_accounts` for core account persistence. 【F:backend/app/routes/plaid_transactions.py†L45-L214】
- **Plaid helper layer**: `plaid_helpers.py` wraps Plaid SDK calls used in the flow (link token creation, public token exchange, item/accounts retrieval). 【F:backend/app/helpers/plaid_helpers.py†L56-L143】
- **Database upsert**: `account_logic.upsert_accounts` normalizes account payloads, writes to `Account` and `AccountHistory`, and logs progress. 【F:backend/app/sql/account_logic.py†L118-L223】
- **Frontend data serving**: After emitting a refresh, the UI pulls `/accounts/get_accounts` through `services/api.js`, which returns normalized account rows for display. 【F:frontend/src/services/api.js†L10-L18】【F:backend/app/routes/accounts.py†L464-L512】

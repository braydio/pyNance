# backend/app/routes Documentation

---

## 📘 `teller.py`

````markdown
# Teller Integration Route

## Purpose

Manages authentication and data ingestion from the Teller API. Facilitates linking of accounts, fetching balances, and initializing webhook updates for real-time financial data.

## Key Endpoints

- `POST /teller/link-token`: Generates a link token for Teller Link.
- `POST /teller/link`: Begins the Teller linking flow using a secure access token.
- `GET /teller/accounts`: Returns user-linked accounts via Teller.
- `GET /teller/balances`: Retrieves current balances from linked accounts.

## Inputs & Outputs

- **POST /teller/link-token**

  - **Input:**
    ```json
    {
      "user_id": "user123"
    }
    ```
  - **Output:** `{ link_token: str }`

- **POST /teller/link**

  - **Input:**
    ```json
    {
      "access_token": "teller-sandbox-abc123"
    }
    ```
  - **Output:** `{ success: true, accounts_linked: int }`

- **GET /teller/accounts**

  - **Output:**
    ```json
    [
      {
        "id": "acct_001",
        "institution": "Bank of America",
        "type": "checking",
        "status": "active"
      }
    ]
    ```

- **GET /teller/balances**
  - **Output:**
    ```json
    {
      "acct_001": { "available": 820.45, "ledger": 850.0 }
    }
    ```

## Internal Dependencies

- `services.teller_client`
- `models.Account`
- `utils.token_store`, `auth.user_context`

## Known Behaviors

- Requires secure exchange of Teller access tokens
- Auto-triggers metadata and transaction sync post-link
- All endpoints are user-scoped and permission-controlled

## Related Docs

- [`docs/dataflow/teller_sync.md`](../../dataflow/teller_sync.md)
- [`docs/integrations/teller_config.md`](../../integrations/teller_config.md)
````

---

Next: `teller_transactions.py`?

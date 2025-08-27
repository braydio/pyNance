# backend/app/routes Documentation

---

## 📘 `plaid_investments.py`

````markdown
# Plaid Investments Route

## Purpose

Facilitates access to investment data via Plaid. Enables viewing of holdings, securities, and current portfolio performance synced from financial institutions.

## Key Endpoints

- `GET /plaid/investments/holdings`: Returns current investment holdings.
- `GET /plaid/investments/securities`: Lists all referenced securities.

## Inputs & Outputs

- **GET /plaid/investments/holdings**

  - **Output:**
    ```json
    [
      {
        "account_id": "plaid_001",
        "symbol": "AAPL",
        "quantity": 15,
        "value": 2895.45,
        "current_price": 193.03
      }
    ]
    ```

- **GET /plaid/investments/securities**
  - **Output:**
    ```json
    [
      {
        "security_id": "sec_123",
        "name": "Apple Inc.",
        "ticker_symbol": "AAPL",
        "type": "equity"
      }
    ]
    ```

## Internal Dependencies

- `services.plaid_client`
- `models.InvestmentHolding`, `models.Security`

## Known Behaviors

- Returns only securities relevant to linked accounts
- Prices and valuations are real-time where available
- Holdings are updated via scheduled sync jobs or manual sync

## Related Docs

- [`docs/dataflow/investment_sync_pipeline.md`](../../dataflow/investment_sync_pipeline.md)
- [`docs/integrations/plaid_investments.md`](../../integrations/plaid_investments.md)
````

---

Next: `plaid_transactions.py`?

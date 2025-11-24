# Plaid Investments Route (`plaid_investments.py`)

## Purpose

Expose Plaid-synced investment holdings and securities so clients can display portfolio composition and valuations.

## Endpoints

- `GET /plaid/investments/holdings` – Return current investment holdings.
- `GET /plaid/investments/securities` – List referenced securities.

## Inputs/Outputs

- **GET /plaid/investments/holdings**
  - **Inputs:** None.
  - **Outputs:** Array of holding objects containing account IDs, symbols, quantities, valuations, and prices.
- **GET /plaid/investments/securities**
  - **Inputs:** None.
  - **Outputs:** Array of security descriptors with IDs, names, ticker symbols, and types.

## Auth

- Requires authenticated user; holdings and securities are filtered to linked accounts.

## Dependencies

- `services.plaid_client` for investment retrieval.
- `models.InvestmentHolding` and `models.Security` for persistence.

## Behaviors/Edge Cases

- Returns only securities relevant to the user's linked accounts.
- Prices and valuations reflect the latest sync (scheduled or manual).

## Sample Request/Response

```http
GET /plaid/investments/holdings HTTP/1.1
```

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

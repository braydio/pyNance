---
Owner: Backend Team
Last Updated: 2026-02-28
Status: Active
---

# Investments Route (`investments.py`)

## Purpose

Expose persisted investment account, holdings, and transaction data under `/api/investments`.

## Endpoints

- `GET /api/investments/accounts`
- `GET /api/investments/holdings`
- `GET /api/investments/transactions`

## Endpoint Contracts

### `GET /api/investments/accounts`

Return all accounts with explicit `Account.is_investment` flags. Responses normalize investment semantics via `account_type = "investment"`.

- Query parameters: none.
- Success response (`200`):

```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "name": "Brokerage",
      "official_name": "Brokerage Individual",
      "type": "investment",
      "subtype": "brokerage",
      "mask": "1234",
      "item_id": "item_..."
    }
  ]
}
```

- Error responses:
  - No explicit route-level error handling is defined; unexpected failures bubble to Flask's default error handling.

### `GET /api/investments/holdings`

Return holdings joined with security metadata.

- Query parameters: none.
- Success response (`200`):

```json
{
  "status": "success",
  "data": [
    {
      "account_id": "acc_...",
      "security_id": "sec_...",
      "quantity": 5,
      "cost_basis": 500.0,
      "institution_value": 625.0,
      "as_of": "2026-02-27",
      "security": {
        "name": "Example Corp",
        "ticker_symbol": "EXM",
        "type": "equity",
        "currency": "USD",
        "price": 125.0,
        "price_as_of": "2026-02-27"
      }
    }
  ]
}
```

- Error responses:
  - No explicit route-level error handling is defined; unexpected failures bubble to Flask's default error handling.

### `GET /api/investments/transactions`

Return paginated investment transactions with optional filters.

- Query parameters:
  - Pagination:
    - `page` (optional, default `1`, integer)
    - `page_size` (optional, default `25`, integer)
  - Filters:
    - `account_id` (optional)
    - `security_id` (optional)
    - `type` (optional)
    - `subtype` (optional)
    - `start_date` (optional, `YYYY-MM-DD`)
    - `end_date` (optional, `YYYY-MM-DD`)
- Filter semantics:
  - `start_date` and `end_date` are parsed to date objects.
  - If both dates are provided and `end_date < start_date`, the request is rejected.
  - Transactions are ordered by `date DESC`.
- Success response (`200`):

```json
{
  "status": "success",
  "data": {
    "transactions": [
      {
        "investment_transaction_id": "itx_...",
        "account_id": "acc_...",
        "security_id": "sec_...",
        "date": "2026-02-25",
        "amount": -100.5,
        "price": 50.25,
        "quantity": 2,
        "subtype": "buy",
        "type": "buy",
        "name": "Example Corp",
        "fees": 0.0,
        "iso_currency_code": "USD"
      }
    ],
    "total": 173,
    "filters": {
      "account_id": "acc_...",
      "security_id": null,
      "type": "buy",
      "subtype": null,
      "start_date": "2026-01-01",
      "end_date": "2026-02-27"
    }
  }
}
```

- Error responses:
  - `400` with shape `{ "status": "error", "error": "..." }` when:
    - `start_date` or `end_date` is not in `YYYY-MM-DD` format.
    - `end_date` is before `start_date`.
  - Non-integer `page` or `page_size` is not explicitly handled in-route and can bubble as an unhandled exception.

## Auth

- No route-level auth checks are implemented in this module.
- Access control, if required, must be enforced by upstream middleware, blueprint wrapping, or deployment boundary.

## Dependencies

- `app.sql.investments_logic.get_investment_accounts` for account reads.
- SQLAlchemy models: `InvestmentHolding`, `Security`, `InvestmentTransaction`.
- Query-param parser helpers in-module:
  - `parse_transaction_filter_params`
  - `_parse_iso_date`

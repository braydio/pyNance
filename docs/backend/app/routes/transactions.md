# Transactions Route (`transactions.py`)

## Purpose
Provide controlled updates, internal transfer discovery, and paginated retrieval helpers for persisted transaction records under `/api/transactions`.

## Endpoints
- `PUT /api/transactions/update` – Update editable transaction attributes and optionally create automation rules.
- `POST /api/transactions/scan-internal` – Identify potential internal transfer pairs without mutation.
- `GET /api/transactions/get_transactions` – Paginated transactions across linked accounts.
- `GET /api/transactions/<account_id>/transactions` – Account-scoped paginated transactions.
- `GET /api/transactions/merchants` – Merchant name suggestions for autocomplete.

## Inputs/Outputs
- **PUT /api/transactions/update**
  - **Inputs:** JSON with `transaction_id` plus editable fields (`amount`, `date`, `description`, `category`, `merchant_name`, `merchant_type`, `is_internal`, `counterpart_transaction_id`, `flag_counterpart`, optional `save_as_rule` metadata).
  - **Outputs:** `{ "status": "success" }` on success; 4xx/5xx envelopes for validation or lookup errors.
- **POST /api/transactions/scan-internal**
  - **Inputs:** None.
  - **Outputs:** `{ "status": "success", "pairs": [...] }` listing likely transfer pairs.
- **GET /api/transactions/get_transactions` and `/api/transactions/<account_id>/transactions`**
  - **Inputs:** Pagination parameters (`page`, `page_size`), optional `start_date`, `end_date`, `category`, `account_ids`, `tx_type`, and `recent=true` for account-specific endpoint.
  - **Outputs:** `{ "status": "success", "data": { "transactions": [...], "total": int } }`.
- **GET /api/transactions/merchants**
  - **Inputs:** Optional `q` substring filter and `limit` (default 50).
  - **Outputs:** `{ "status": "success", "data": ["Merchant", ...] }`.

## Auth
- Requires authenticated user; all queries are scoped to the user's linked accounts.

## Dependencies
- Decimal helpers (`TWOPLACES`, `AMOUNT_EPSILON`) for currency precision.
- `transaction_rules_logic` for optional rule creation.
- Date parsing helpers (`_parse_iso_datetime`, `_ensure_utc`) to normalize filters.

## Behaviors/Edge Cases
- Update endpoint marks `user_modified` fields and normalizes amounts/dates.
- Internal transfer scanning looks ±1 day for negating amounts within `±0.01`.
- Legacy compatibility: `/api/transactions/user_modify/update` mirrors the update contract.

## Sample Request/Response
```http
PUT /api/transactions/update HTTP/1.1
Content-Type: application/json

{ "transaction_id": "txn_1", "amount": -25.50, "category": "groceries", "save_as_rule": true }
```

```json
{ "status": "success" }
```

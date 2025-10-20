## 📘 `transactions.py`

The `transactions` blueprint is mounted at `/api/transactions` and complements
analytics exports by giving consumers targeted ways to adjust persisted
transactions or surface likely internal transfers. The module focuses on
post-processing workflows (annotation, reconciliation, matching) rather than
full CRUD creation/deletion.

### Helper utilities

- `_parse_iso_datetime` normalises ISO 8601 strings (with or without timezone
  info) into timezone-aware UTC `datetime` objects.
- `_ensure_utc` safely attaches UTC information to naive `datetime` instances
  created from `YYYY-MM-DD` filters.
- Decimal helpers (`TWOPLACES`, `AMOUNT_EPSILON`) enforce currency precision
  and support approximate amount comparisons when matching transfers.

### Endpoints

#### `PUT /api/transactions/update`

Update a single transaction's editable attributes.

- **Request body** (JSON):
  - `transaction_id` _(required)_ – identifier of the record to update.
  - Optional mutation fields: `amount`, `date`, `description`, `category`,
    `merchant_name`, `merchant_type`, `is_internal`.
  - Internal-transfer helpers:
    - `counterpart_transaction_id` – link another transaction when
      `is_internal` is `true`.
    - `flag_counterpart` – when `true`, mirror the `is_internal` flag onto the
      counterpart transaction.
  - **Rule authoring (optional):**
    - Set `save_as_rule: true` to persist a reusable rule scoped to the
      transaction owner.
    - `rule_field` / `rule_value` describe the attribute to apply (currently
      category or merchant metadata).
    - `rule_description` seeds an exact-match description pattern if provided.
    - `rule_account_id` scopes matching to a specific account (defaults to the
      updated transaction's account).
- **Behaviour:**
  - Validates decimal amounts and ISO timestamps.
  - Marks `user_modified` and tracks which fields changed in
    `user_modified_fields` for downstream auditability.
  - When rule creation is requested, delegates to
    `transaction_rules_logic.create_rule` with the derived match criteria and
    action payload.
- **Responses:**
  - `200` with `{ "status": "success" }` on success.
  - `4xx` with an error message when validation fails or the transaction does
    not exist.
  - `500` on unexpected exceptions (also logged).

> 🔁 **Legacy path:** `/api/transactions/user_modify/update` exposes the same
> mutation logic for older clients.

#### `POST /api/transactions/scan-internal`

Identify potential pairs of internal transfers without mutating database
records.

- **Request body:** none required.
- **Processing:** scans non-internal transactions for matches owned by the same
  user in a ±1 day window with offsetting amounts (within `±0.01`).
- **Response:** `200` with `{ "status": "success", "pairs": [ ... ] }`. Each
  pair includes both transaction identifiers, signed amounts, ISO dates, and
  descriptions to assist manual review. Errors yield `{ "status": "error" }`
  with the exception message.

#### `GET /api/transactions/get_transactions`

Return paginated transactions across the user's accounts.

- **Query parameters:**
  - `page` _(default 1)_, `page_size` _(default 15)_.
  - `start_date`, `end_date` (`YYYY-MM-DD`, inclusive).
  - `category` – optional category filter.
  - `account_ids` – comma-separated account identifiers.
  - `tx_type` (or legacy alias `type`) – filter credits or debits.
- **Response:** `200` with `{ "status": "success", "data": { "transactions":
[...], "total": <int> } }`.

#### `GET /api/transactions/<account_id>/transactions`

Fetch transactions for a specific account with the same pagination schema.

- **Query parameters:**
  - `page`, `page_size`, `start_date`, `end_date`, `category` (as above).
  - `recent=true` bypasses date filters and caps the result using `limit`
    _(default 10)_.
- **Response:** `200` with the same payload shape as the collection endpoint.

#### `GET /api/transactions/merchants`

Provide merchant name suggestions for autocomplete UIs.

- **Query parameters:**
  - `q` – optional case-insensitive substring match.
  - `limit` – maximum results (default 50).
- **Response:** `200` with `{ "status": "success", "data": ["Merchant", ...] }`.

### Workflow notes

- **User-authored rules:** The update route can persist transaction rules
  directly from the request when categorisation changes should be reused.
  Document clients should surface the optional `save_as_rule` controls when
  editing a transaction so power users can automate repetitive clean-up.
- **Internal transfer reconciliation:** Consumers can call
  `/api/transactions/scan-internal` prior to marking transactions as internal.
  The response payload contains enough context to confirm matches before
  issuing follow-up `PUT /api/transactions/update` requests that set
  `is_internal` and link the counterpart identifiers.

### Related references

- [`backend/app/routes/transactions.py`](../../../backend/app/routes/transactions.py)
- [`docs/backend/features/transaction_rules.md`](../../backend/features/transaction_rules.md)
- [`docs/API_REFERENCE.md`](../../API_REFERENCE.md)

## 📘 `transactions.py`

The `transactions` blueprint is mounted at `/api/transactions` and provides
post-processing tools for persisted transaction records. The module focuses on
controlled updates, discovery of internal transfers, and paginated retrieval
helpers that power dashboard views and downstream exports.

### Helper utilities

- `_parse_iso_datetime(value)` normalises ISO 8601 strings (with or without
  timezone info) into timezone-aware UTC `datetime` objects.
- `_ensure_utc(dt)` attaches UTC to naive `datetime` instances that come from
  `YYYY-MM-DD` filters so range comparisons behave as expected.
- Decimal helpers (`TWOPLACES`, `AMOUNT_EPSILON`) enforce currency precision and
  allow near-zero comparisons when matching transfer pairs.

### Endpoints

#### `PUT /api/transactions/update`

Update a single transaction's editable attributes. Requires a JSON body with at
least `transaction_id` and any combination of mutable fields.

- **Editable fields**: `amount`, `date`, `description`, `category`,
  `merchant_name`, `merchant_type`, `is_internal`.
- **Internal transfer helpers**:
  - `counterpart_transaction_id` (string) — ID of the matching transfer when
    `is_internal` is `true`.
  - `flag_counterpart` (bool, default `false`) — when set, mirrors the
    `is_internal` flag and `internal_match_id` onto the counterpart record.
- **Rule authoring (optional)**:
  - `save_as_rule: true` enables rule creation after the transaction is updated.
  - `rule_field` / `rule_value` describe which attribute to set when the rule
    runs. Supported fields align with the editable transaction attributes.
  - `rule_description` seeds an exact-match description regex when provided.
  - `rule_account_id` scopes matching to a specific account (defaults to the
    updated transaction's account).

**Behaviour**

- Validates decimal amounts (quantised to two places) and ISO timestamps.
- Marks `user_modified` and maintains a JSON blob of `user_modified_fields` to
  track which attributes changed.
- When rule creation is requested, delegates to
  `transaction_rules_logic.create_rule(user_id, match_criteria, action)` using
  the derived account scope and description pattern.

**Responses**

- `200` with `{ "status": "success" }` on success.
- `400` for malformed payloads (missing `transaction_id`, bad amount/date).
- `404` when the target transaction is not found.
- `500` on unexpected exceptions (logged with stack traces).

> 🔁 **Legacy compatibility:** `/api/transactions/user_modify/update` retains the
> same request and response contract for older clients.

#### `POST /api/transactions/scan-internal`

Identify potential pairs of internal transfers without mutating database
records.

- **Request body**: none required.
- **Processing**: scans transactions that are not flagged as internal. For each
  transaction, it looks ±1 day for another account owned by the same user whose
  amount negates the source within `±0.01`.
- **Response**: `200` with `{ "status": "success", "pairs": [ ... ] }`. Each
  entry includes both transaction IDs, signed amounts, ISO dates, and
  descriptions plus a nested `counterpart` object for quick UI presentation.
  Errors return `{ "status": "error", "message": "..." }`.

#### `GET /api/transactions/get_transactions`

Return paginated transactions across the user's linked accounts.

- **Query parameters**:
  - `page` (default `1`), `page_size` (default `15`).
  - `start_date`, `end_date` — inclusive `YYYY-MM-DD` bounds; converted to UTC
    datetimes and support open-ended ranges.
  - `category` — optional category filter.
  - `account_ids` — comma-separated account identifiers.
  - `tx_type` (or legacy alias `type`) — filter to `credit` or `debit`.
- **Response**: `200` with `{ "status": "success", "data": { "transactions":
[...], "total": <int> } }`.

#### `GET /api/transactions/<account_id>/transactions`

Fetch transactions for a specific account with the same pagination schema.

- **Query parameters**:
  - `page`, `page_size`, `start_date`, `end_date`, `category` as above.
  - `recent=true` bypasses date filters and caps the response using `limit`
    (default `10`).
- **Response**: `200` with `{ "status": "success", "data": { "transactions":
[...], "total": <int> } }`.

#### `GET /api/transactions/merchants`

Provide merchant name suggestions for autocomplete experiences.

- **Query parameters**:
  - `q` — optional case-insensitive substring filter.
  - `limit` — maximum results (default `50`).
- **Response**: `200` with `{ "status": "success", "data": ["Merchant", ...] }`.

### Workflow integrations

- **User-authored rules**: Clients can surface the `save_as_rule` controls in
  the update workflow so that recurring corrections become automated.
  Rules inherit the transaction's account by default and may capture an exact
  description match for precision updates.
- **Internal transfer reconciliation**: Consumers should call
  `/api/transactions/scan-internal` to discover likely transfer pairs and then
  submit `PUT /api/transactions/update` requests (optionally with
  `counterpart_transaction_id` and `flag_counterpart`) to mark them as internal.

### Related references

- [`backend/app/routes/transactions.py`](../../../backend/app/routes/transactions.py)
- [`docs/backend/features/transaction_rules.md`](../../backend/features/transaction_rules.md)
- [`docs/API_REFERENCE.md`](../../API_REFERENCE.md)

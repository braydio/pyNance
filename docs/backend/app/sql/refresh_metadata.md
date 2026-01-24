# backend/app/sql/refresh_metadata.py

## Purpose

Upsert Plaid transaction metadata into `PlaidTransactionMeta`, normalizing dates and
serializing complex payload fields for storage.

## Key Responsibilities

- Coerce Plaid date and datetime fields into consistent types.
- Sanitize nested payloads into JSON-safe primitives.
- Insert or update metadata rows tied to a `Transaction`.

## Primary Functions

- `_coerce_date(value)`
  - Accepts `date`, `datetime`, ISO date strings, or `None`.
- `_coerce_datetime(value)`
  - Accepts `datetime`, `date`, ISO datetime strings, or `None`; ensures tz-aware values.
- `_sanitize_for_json(value)`
  - Recursively converts dict/list/tuple/dates/datetimes into JSON-safe primitives.
- `refresh_or_insert_plaid_metadata(plaid_tx, transaction, plaid_account_id)`
  - Upserts a `PlaidTransactionMeta` row for a single transaction; does not commit.
- `batch_refresh_plaid_metadata(plaid_tx_list, transaction_map, plaid_account_id)`
  - Upserts metadata for a batch of transactions; does not commit.

## Inputs

- Plaid transaction dicts (raw API payloads).
- SQLAlchemy `Transaction` instances.
- `plaid_account_id` for the Plaid account foreign key.

## Outputs

- `PlaidTransactionMeta` model instances (single or list).

## Internal Dependencies

- `app.models.PlaidTransactionMeta`
- `app.extensions.db`

## Known Behaviors

- Stores the raw Plaid payload under `meta.raw` after sanitization.
- Sets `meta.is_active = True` on every refresh.
- Does not commit the session; callers are responsible for committing.

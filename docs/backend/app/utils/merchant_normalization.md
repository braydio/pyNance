# `merchant_normalization.py`

## Purpose

Provide a shared merchant normalization helper so both Plaid ingestion paths produce
consistent merchant labels even when transaction descriptions include processor noise.

## Fallback Resolution Order

1. Use Plaid `merchant_name` when present and non-empty.
2. Otherwise parse Plaid `name`.
3. Otherwise parse Plaid `description`.
4. Fall back to `Unknown` when all merchant sources are empty.

## Normalization Rules

- Strip common payment/processor prefixes such as `POS`, `SQ *`, `PAYPAL *`,
  `PP*`, `TST*`, and `CARD ####`.
- Remove separator tails (for example values after `-`, `/`, `:`, or `|`) and
  trailing generic tokens (`pending`, `purchase`, `online`, `ach`, etc.).
- Collapse whitespace and normalize output casing for display.
- Emit:
  - `display_name`: normalized merchant label for `Transaction.merchant_name`.
  - `merchant_slug`: lowercase slug for deterministic matching and metadata.

## Usage

Called by both:

- `backend/app/sql/account_logic.py::refresh_data_for_plaid_account`
- `backend/app/services/plaid_sync.py::_upsert_transaction`

Both ingestion paths preserve the original source description (`name`/`description`)
in `Transaction.description` while storing normalized merchant values.

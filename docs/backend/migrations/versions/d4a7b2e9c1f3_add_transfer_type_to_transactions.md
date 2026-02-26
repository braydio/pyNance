# `d4a7b2e9c1f3_add_transfer_type_to_transactions`

- Source: `backend/migrations/versions/d4a7b2e9c1f3_add_transfer_type_to_transactions.py`
- Revision: `d4a7b2e9c1f3`
- Down revision: `c2f8d9a4e1b7`

## Purpose

Adds explicit transfer classification metadata to the `transactions` table.

## Schema changes

- Adds nullable `transactions.transfer_type` (`VARCHAR(32)`).
- Adds non-unique index `ix_transactions_transfer_type` for reporting and filtering.

## Rollback

Downgrade drops the index and removes the `transfer_type` column.

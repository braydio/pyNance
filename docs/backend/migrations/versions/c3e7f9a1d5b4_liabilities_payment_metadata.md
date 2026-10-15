# Migration `c3e7f9a1d5b4` - Plaid Liabilities payment metadata

## Summary

Adds nullable cached payment/statement metadata populated only from an authorized Plaid `/liabilities/get`. No backfill.

## Schema changes

`accounts.minimum_payment_amount` (`NUMERIC(18,2)`), `next_payment_due_date` (`DATE`), `statement_balance` (`NUMERIC(18,2)`), `statement_date` (`DATE`), `liabilities_status` (`VARCHAR(24)`: `ok`, `no_rates_reported`, `unavailable`, `stale`), `liabilities_as_of` (`TIMESTAMPTZ`). All nullable.

## Rollback

Downgrade drops the six columns (idempotent). Revises `b2d6e8f0c4a3`.

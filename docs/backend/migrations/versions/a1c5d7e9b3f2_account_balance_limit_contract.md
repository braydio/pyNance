# Migration `a1c5d7e9b3f2` - Account balance, limit and freshness contract

## Summary

Adds nullable provider-observed balance metadata to `accounts`. No backfill: existing rows keep `NULL`, which the API reports as "unknown" rather than zero.

## Schema changes

- `accounts.credit_limit` (`NUMERIC(18,2) NULL`) - provider credit line, credit products only.
- `accounts.available_balance` (`NUMERIC(18,2) NULL`) - provider "available" figure as reported.
- `accounts.mask` (`VARCHAR(8) NULL`).
- `accounts.currency_code` (`VARCHAR(8) NULL`).
- `accounts.balance_as_of` (`TIMESTAMPTZ NULL`) - when `balance` was last observed.

## Rollback

Downgrade drops the five columns (idempotent; skips missing columns). Revises `f84c6e2a91b7`.

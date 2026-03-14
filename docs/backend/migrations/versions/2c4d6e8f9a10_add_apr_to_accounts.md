# Migration `2c4d6e8f9a10` — add APR to accounts

## Summary

Adds a nullable `apr` numeric column to the `accounts` table so account payloads can persist provider APR values or inferred APR estimates from transaction analysis.

## Schema changes

- `upgrade()`
  - Adds `accounts.apr` as `NUMERIC(7, 4)`, nullable.
- `downgrade()`
  - Drops `accounts.apr`.

## Rationale

The accounts UI includes an APR section for credit liabilities. This migration introduces a first-class storage field that supports both direct provider APR values and runtime APR inference based on interest-charge transactions.

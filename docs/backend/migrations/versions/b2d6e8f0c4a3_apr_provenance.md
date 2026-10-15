# Migration `b2d6e8f0c4a3` - APR provenance metadata

## Summary

Adds provenance columns next to `accounts.apr` so a rate always says where it came from.

## Schema changes

- `accounts.apr_source` (`VARCHAR(32) NULL`): `provider`, `manual`, `estimated`, `legacy_unverified`.
- `accounts.apr_as_of` (`TIMESTAMPTZ NULL`), `accounts.apr_confidence` (`VARCHAR(16) NULL`), `accounts.apr_sample_cycles` (`INTEGER NULL`).
- `accounts.apr_details` (`JSON NULL`): per-bucket rates for multi-APR cards.

## Data change

Rows with a non-null `apr` and no source are marked `legacy_unverified` (the previous value was inferred from a single interest charge or entered without provenance). No values are modified or deleted. `apr` is stored in percentage units (`23.49` = 23.49%).

## Rollback

Downgrade drops the five columns (idempotent). Revises `a1c5d7e9b3f2`.

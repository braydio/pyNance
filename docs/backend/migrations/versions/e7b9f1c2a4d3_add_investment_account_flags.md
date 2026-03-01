# Migration `e7b9f1c2a4d3` - Add investment account flags

## Summary

Adds explicit investment metadata columns to `accounts` so API and SQL layers can rely on deterministic flags instead of string inference.

## Schema changes

- Adds `accounts.is_investment` (`BOOLEAN NOT NULL DEFAULT false`).
- Adds `accounts.investment_has_holdings` (`BOOLEAN NOT NULL DEFAULT false`).
- Adds `accounts.investment_has_transactions` (`BOOLEAN NOT NULL DEFAULT false`).
- Adds `accounts.product_provenance` (`VARCHAR(64) NULL`).

## Rollback

Downgrade removes the four columns in reverse order.

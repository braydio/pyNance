# Migration: `c2f8d9a4e1b7_add_canonical_transaction_categories.py`

## Summary

Introduces canonical category identity fields and backfills existing data.

- Adds `categories.category_slug` and `categories.category_display`.
- Adds `transactions.category_slug` and `transactions.category_display`.
- Backfills canonical values from existing legacy/PFC category fields.
- Deduplicates `categories` rows that normalize to the same canonical slug and repoints `transactions.category_id` to the retained row.
- Adds indexes for canonical slug lookups (`categories` unique, `transactions` non-unique).

## Operational impact

After upgrade, analytics and top-category grouping can rely on stable canonical category keys even when incoming display strings vary across Plaid payload formats.

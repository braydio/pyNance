# Migration: `a7c1d9e2f4b8_add_transaction_merchant_slug.py`

## Summary

Adds canonical merchant key persistence to transaction records.

## Changes

- Adds nullable `transactions.merchant_slug` column.
- Adds non-unique index `ix_transactions_merchant_slug` to support analytics grouping queries.

## Why

Top-spending analytics now groups merchants by canonical slug for stable buckets when display names vary across providers and user edits.

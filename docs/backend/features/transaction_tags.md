---
Owner: Backend Team
Last Updated: 2026-01-11
Status: Active
---

# Transaction Tags

## Purpose

Transaction tags allow users to apply free-form labels to transactions for filtering and grouping.
Tags are stored per user and associated to transactions through a join table.

## Data Model

- **Tag** (`backend/app/models/transaction_models.py`)
  - `id` – Primary key
  - `user_id` – Tag owner
  - `name` – Tag label, unique per user
  - `created_at` / `updated_at` – Timestamp mixin fields
- **transaction_tags** (`backend/app/models/transaction_models.py`)
  - `transaction_id` – Foreign key to `transactions.transaction_id`
  - `tag_id` – Foreign key to `tags.id`

## Default Tag Behavior

Transactions without tags are serialized with a default `#untagged` label in
`backend/app/sql/account_logic.get_paginated_transactions`.
This keeps downstream consumers consistent without requiring a stored tag row
for every transaction. The update endpoint can also normalize blank tag edits
to `#untagged` so the association remains explicit after user edits.

## Serialization Notes

`get_paginated_transactions` returns a `tags` field as a list of tag names on
each transaction. When no tags exist, the list is `["#untagged"]`.

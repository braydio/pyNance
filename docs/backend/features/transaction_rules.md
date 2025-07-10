# Transaction Rules Guide

Transaction rules let users automatically modify transactions during sync based on pattern matching.

## Overview

- **Model**: `TransactionRule`
- **Purpose**: Persist user-defined criteria that trigger updates on incoming transactions.
- **Location**: `backend/app/models.py` and accompanying SQL helpers.

## Rule Fields

- `id` – Primary key
- `user_id` – Owner of the rule
- `match_criteria` – JSON object containing one or more of:
  - `merchant_name`
  - `description_pattern`
  - `amount_min` / `amount_max`
- `action` – JSON describing applied changes (e.g., `{ "category_id": "...", "merchant": "Starbucks" }`)
- `created_at` / `updated_at` – Timestamps

## Workflow

1. **Create Rule** – User edits a transaction and chooses "Save as rule". The backend stores criteria and action in `TransactionRule`.
2. **Apply Rule** – During transaction ingestion (`account_logic.get_paginated_transactions` or similar), rules matching the new transaction are loaded and executed before commit.
3. **Manage Rule** – CRUD endpoints under `/api/rules` allow listing, updating, disabling, or deleting rules.

When a rule updates a transaction, the record is marked with `updated_by_rule=true` so the UI can show the automated classification.

## Endpoints Summary

- `GET /rules` – List rules for the current user.
- `POST /rules` – Create a rule from provided criteria and action.
- `PATCH /rules/<id>` – Modify rule parameters or enable/disable it.
- `DELETE /rules/<id>` – Remove a rule entirely.

These endpoints complement the existing `/transactions/update` flow.


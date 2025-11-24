# Institutions Route (`institutions.py`)

## Purpose

Provide institution-level aggregates and refresh operations for linked financial accounts, combining ORM data with Plaid refresh utilities.

## Endpoints

- `GET /api/institutions/` – List institutions with linked accounts, normalized balances, and refresh timestamps.
- `POST /api/institutions/<institution_id>/refresh` – Trigger Plaid refreshes for all accounts under an institution.

## Inputs/Outputs

- **GET /api/institutions/**
  - **Inputs:** None.
  - **Outputs:** `{ "status": "success", "institutions": [...] }` with balances and account details.
- **POST /api/institutions/<institution_id>/refresh**
  - **Inputs:** Optional JSON `start_date` and `end_date` for scoping backfills.
  - **Outputs:** `{ "status": "success", "updated_accounts": int, "refresh_counts": {...} }` summarizing processed accounts.

## Auth

- Requires authenticated user; institution data is scoped to linked accounts for that user.

## Dependencies

- `app.models.Institution` for ORM access to institutions and accounts.
- `app.sql.account_logic.refresh_data_for_plaid_account` and related Plaid helpers.
- `app.utils.finance_utils.normalize_account_balance` and `app.extensions.db` for calculations and persistence.

## Behaviors/Edge Cases

- Only Plaid-linked accounts are refreshed; unsupported accounts are skipped.
- Refresh timestamps are written only when at least one account updates successfully.

## Sample Request/Response

```http
POST /api/institutions/123/refresh HTTP/1.1
Content-Type: application/json

{ "start_date": "2024-01-01", "end_date": "2024-02-01" }
```

```json
{ "status": "success", "updated_accounts": 2, "refresh_counts": { "plaid": 2 } }
```

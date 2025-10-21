# Institutions Route

## Purpose

Surface institution-level aggregates and refresh operations that coordinate
linked financial accounts. The blueprint composes ORM data with Plaid refresh
utilities so the UI can display grouped balances and trigger data pulls.

## Key Endpoints

- `GET /api/institutions/` – Enumerate institutions with their linked accounts,
  normalized balances, and the most recent Plaid refresh timestamp.
- `POST /api/institutions/<institution_id>/refresh` – Iterate each account under
  an institution and invoke Plaid refresh logic when applicable, updating the
  `last_refreshed` timestamp.

## Inputs & Outputs

- Refresh requests accept optional `start_date` and `end_date` in the JSON body
  to scope Plaid transaction backfills.
- Responses return `{ "status": "success", "institutions": [...] }` for list
  calls and include `updated_accounts` plus per-institution refresh counts for
  refreshes.

## Internal Dependencies

- `app.models.Institution` for ORM access to institutions and related accounts
- `app.sql.account_logic.refresh_data_for_plaid_account`
- `app.utils.finance_utils.normalize_account_balance`
- `app.extensions.db` for commit/rollback semantics

## Known Behaviors

- Only accounts linked through Plaid are refreshed; others are skipped quietly.
- Refresh timestamps use `datetime.now()` and are persisted only when at least
  one account updates successfully.

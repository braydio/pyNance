# `institutions.py`

Institution-centric API providing grouped account information and refresh
controls. Registered at `/api/institutions`.

## Dependencies

- `app.models.Institution` and related `Account`/`PlaidAccount` relationships.
- `app.utils.finance_utils.normalize_account_balance` for consistent balance
  presentation.
- `app.sql.account_logic.refresh_data_for_plaid_account` to trigger Plaid data
  refreshes per account.
- `app.extensions.db` for session management.

## Endpoints

| Method | Path                                         | Description                                                                                                                                                              |
| ------ | -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `GET`  | `/api/institutions/`                         | Lists institutions with aggregated account details (balance, type, last refreshed timestamp).                                                                            |
| `POST` | `/api/institutions/<institution_id>/refresh` | Iterates the institution's accounts, refreshing Plaid-linked accounts via `refresh_data_for_plaid_account`. Optional JSON body supports `start_date`/`end_date` filters. |

## Behaviour Notes

- Last refreshed timestamps are updated using `datetime.now()` when at least one
  account refresh succeeds; otherwise the session is rolled back to avoid
  accidental partial updates.
- Only Plaid-linked accounts (`link_type == "plaid"`) are refreshed; others are
  skipped silently.

# `accounts_service.py`

## Responsibility

- Provide a focused helper for fetching Plaid account data during refresh flows.
- Keep route-level refresh orchestration decoupled from the Plaid helper implementation.

## Key Functions

- [`fetch_accounts(access_token, user_id)`](../../../../backend/app/services/accounts_service.py): Delegates to Plaid helpers to return account data for the user or `None` on rate-limit handling.

## Dependencies & Collaborators

- [`app.helpers.plaid_helpers.get_accounts`](../../../../backend/app/helpers/plaid_helpers.py) for the Plaid API integration.
- Refresh orchestration in [`routes/accounts.py`](../routes/accounts.md) calls this helper during bulk and single-account refresh flows.

## Usage Notes

- Callers should handle `None` responses as rate-limit or upstream failures and surface user-facing retry guidance.
- Returned account objects may be Plaid SDK types; routes normalize them into dictionaries before further processing.

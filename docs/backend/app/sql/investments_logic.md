# backend/app/sql/investments_logic.py

## Purpose

Persist Plaid investments data (securities, holdings, and investment transactions)
and expose basic account lookups for investment-enabled accounts.

## Key Responsibilities

- Normalize Plaid payloads into JSON-safe structures for storage.
- Upsert securities and holdings fetched from Plaid.
- Upsert investment transactions from Plaid transaction payloads.

## Primary Functions

- `_json_safe(obj)`
  - Recursively converts datetimes, dates, decimals, lists, and dicts for JSON storage.
- `get_investment_accounts()`
  - Returns accounts tied to Plaid investment products.
- `upsert_investments_from_plaid(user_id, access_token)`
  - Fetches Plaid investments, upserts securities and holdings, commits the session.
- `upsert_investment_transactions(items)`
  - Upserts investment transactions via `db.session.merge`, commits, returns count.

## Inputs

- Plaid access token (for fetching investments).
- Plaid investment payloads (securities, holdings, transactions).

## Outputs

- Account dicts, summary counts, or processed transaction counts depending on function.

## Internal Dependencies

- `app.models.Security`, `InvestmentHolding`, `InvestmentTransaction`, `PlaidAccount`, `Account`
- `app.extensions.db`
- `app.helpers.plaid_helpers.get_investments`

## Known Behaviors

- Holdings use PostgreSQL `ON CONFLICT` upserts on `(account_id, security_id)`.
- Securities and transactions use SQLAlchemy `merge` for upserts.
- Commits the session within the upsert helpers.

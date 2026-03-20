# backend/app/sql/investments_logic.py

## Purpose

Persist Plaid investments data (securities, holdings, and investment transactions)
and expose basic account lookups for investment-enabled accounts.

## Key Responsibilities

- Normalize Plaid payloads into JSON-safe structures for storage.
- Upsert securities and holdings fetched from Plaid.
- Upsert investment transactions from Plaid transaction payloads.
- Orchestrate a full Plaid investments refresh inside one transaction boundary.

## Primary Functions

- `_json_safe(obj)`
  - Recursively converts datetimes, dates, decimals, lists, and dicts for JSON storage.
- `get_investment_accounts()`
  - Returns accounts tied to Plaid investment products.
- `upsert_investment_holdings(securities, holdings, commit=True)`
  - Persists securities and holdings and optionally leaves commit control to the caller.
- `upsert_investments_from_plaid(user_id, access_token, commit=True)`
  - Fetches Plaid investments, delegates to the holdings helper, and optionally commits.
- `upsert_investment_transactions(items, commit=True)`
  - Upserts investment transactions via `db.session.merge`, optionally commits, and returns the processed count.
- `sync_investments_from_plaid(user_id, access_token, start_date, end_date, commit=True)`
  - Fetches holdings plus transactions and persists all three investment datasets in a single transaction.

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
- Low-level upsert helpers accept `commit=False` so routes/services can own the transaction boundary.
- The orchestration helper can roll back securities, holdings, and investment transactions together when any stage fails.

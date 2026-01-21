# Plaid Token Linking Script

## scripts/plaid_link_from_token.py

Purpose

- Link Plaid accounts from stored access tokens and ensure `Account` and `PlaidAccount` rows exist.

Inputs

- Token file containing a list of objects with `user_id` and `access_token`.
- Defaults to `FILES["PLAID_TOKENS"]` from `app.config`.

Usage

```bash
python scripts/plaid_link_from_token.py [token_file]
```

Token File Format

```json
[
  { "user_id": "user-123", "access_token": "access-sandbox-..." },
  { "user_id": "user-456", "access_token": "access-sandbox-..." }
]
```

Behavior

- Loads the standard Flask app via `create_app()` and runs within an app context.
- For each token, fetches Plaid item/account metadata, upserts accounts, and inserts missing `PlaidAccount` records.
- Commits inserts per run and logs the count of inserted/updated accounts.

Notes

- Requires `SQLALCHEMY_DATABASE_URI` and Plaid credentials (`PLAID_CLIENT_ID`, `PLAID_SECRET_KEY`) to be configured.
- Uses the normal app factory, so development/test schema setup runs when `ENV` is set to `development` or `test`.
- Designed for one-off or maintenance usage; it is not a Flask CLI command.

## 📘 `import_plaid_tokens.py`
```markdown
# Import Plaid Tokens from CSV

Imports `account_id,access_token,item_id` triples into both `plaid_items` and
`plaid_accounts`. This is intended for loading legacy access tokens exported
from an older deployment.

**Location:** `backend/app/cli/import_plaid_tokens.py`

## Expected Columns

- `account_id`
- `access_token`
- `item_id`

All three are required per row. Rows with missing data, or whose `account_id`
cannot be found in `accounts`, are skipped.

## Usage

From the `backend/` directory:

```bash
flask import-plaid-tokens
# or with an explicit path
flask import-plaid-tokens --csv-path app/data/PlaidAccessTokens.csv
```

The command:

- Upserts a `PlaidItem` per `item_id` with the given `access_token`.
- Upserts a `PlaidAccount` per `account_id` pointing at the same `item_id`
  and token.
```


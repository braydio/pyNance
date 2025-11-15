## 📘 `backfill_plaid_history.py`

````markdown
# Backfill Plaid Transaction History

CLI helper for pulling long-range transaction history from Plaid into the
`transactions` table by driving the existing
`refresh_data_for_plaid_account()` helper with an explicit date range.

**Location:** `backend/app/cli/backfill_plaid_history.py`

## Usage

Invoke via Flask's CLI from the `backend/` directory (with `FLASK_APP=run.py`):

- Backfill a single Plaid account:

  ```bash
  flask backfill-plaid-history --account <ACCOUNT_ID> --start 2018-01-01
  ```
````

- Backfill all accounts for a given Plaid Item:

  ```bash
  flask backfill-plaid-history --item <ITEM_ID> --start 2023-01-01
  ```

- Backfill all Plaid accounts (one representative account per item):

  ```bash
  flask backfill-plaid-history --start 2023-01-01
  ```

`--end` defaults to today when omitted. All calls reuse the same filtering
rules as the normal refresh pipeline (hidden accounts and internal transfers
are excluded).

```

```

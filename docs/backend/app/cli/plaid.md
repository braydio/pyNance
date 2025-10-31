# `plaid` CLI utilities

```markdown
The Plaid maintenance scripts live under `backend/app/cli/` and cover:

- [`get_plaid_institutions.py`](../../../../backend/app/cli/get_plaid_institutions.py)
  exports institution metadata to CSV for operators.
- [`map_and_update_institutions.py`](../../../../backend/app/cli/map_and_update_institutions.py)
  reconciles stored Plaid accounts against institution records.
- [`sync_plaid_transactions.py`](../../../../backend/app/cli/sync_plaid_transactions.py)
  provides Click commands for ad-hoc Plaid refreshes.

Each script is safe to invoke with `flask --app backend.run` or via the
packaged Click entrypoints documented in `scripts/sync.md`.
```

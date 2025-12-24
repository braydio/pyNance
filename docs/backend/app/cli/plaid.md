# `plaid` CLI utilities

```markdown
The Plaid maintenance scripts live under `backend/app/cli/` and cover:

- [`get_plaid_institutions.py`](../../../../backend/app/cli/get_plaid_institutions.py)
  exports institution metadata to CSV for operators.
- [`map_and_update_institutions.py`](../../../../backend/app/cli/map_and_update_institutions.py)
  reconciles stored Plaid accounts against institution records.
- [`sync_plaid_transactions.py`](../../../../backend/app/cli/sync_plaid_transactions.py)
  provides Click commands for ad-hoc Plaid refreshes.
- [`reconcile_plaid_items.py`](../../../../backend/app/cli/reconcile_plaid_items.py)
  verifies locally stored Plaid items via `/item/get` and reports any tokens that
  need to be rotated or re-authenticated.

Each script is safe to invoke with `flask --app backend.run` or via the
packaged Click entrypoints documented in `scripts/sync.md`.
```

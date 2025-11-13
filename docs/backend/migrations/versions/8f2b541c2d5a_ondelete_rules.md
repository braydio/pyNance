# Align ON DELETE rules with application behavior

This migration updates foreign key `ondelete` actions to match how the API manages related records.

- Revision: `8f2b541c2d5a`
- Depends on: `4b9af1d3db6d`
- Source: `backend/migrations/versions/8f2b541c2d5a_ondelete_rules.py`

Highlights:

- Uses `CASCADE` for relations where child rows should be removed with their parent (e.g., accounts → account_history, transactions, plaid artifacts).
- Uses `SET NULL` where historical data should be retained without a parent (e.g., transactions → categories, some investment links).
- Includes conditional handling for optional tables (e.g., `teller_accounts`).

Downgrade restores the previous constraints without explicit `ondelete` behavior.

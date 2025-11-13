# Remove Teller integration artifacts

This migration removes the deprecated Teller integration from the schema and tightens related enums to Plaid/manual only.

- Revision: `f3d2c4a1b6e7`
- Depends on: `9d3f4c21a7b9`
- Source: `backend/migrations/versions/f3d2c4a1b6e7_remove_teller_integration.py`

Actions performed:

- Normalize legacy values to supported enum variants using safe casts:
  - `accounts.link_type`: set any `teller` values to `manual`.
  - `transactions.provider`: set any `teller` values to `manual`.
- Rebuild enum types without the `teller` label and re-cast columns:
  - `link_type`: now `manual | plaid`.
  - `provider_type`: now `manual | plaid`.
- Drop the `teller_accounts` table if present.

Notes:

- Comparisons are done via `::text` and assignments cast back to the enum type to avoid Postgres invalid-literal errors.
- This migration is a follow-up to `9d3f4c21a7b9` which introduced the enums and broader schema hardening.

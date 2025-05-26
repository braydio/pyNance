# 🔍 Transactions Routing Refactor Exposure Map

## 📁 Component: `routes/plaid_transactions.py`

### ✅ Exposed Functions (Impacted by Refactor)

These functions contain Plaid-specific transaction logic and will be restructured under:
`providers/plaid.py`

- `generate_link_token_endpoint()`
  Generates link tokens for onboarding.
- `exchange_public_token_endpoint()`
  Exchanges public token and syncs Plaid account data.
- `refresh_plaid_accounts()`
  Re-fetches Plaid account and category information.
- `delete_plaid_account()`
  Deletes synced Plaid account data from local DB.

### ⚠️ Partial Exposure

- `refresh_plaid_accounts()` also includes helper logic tied to user-specific account hydration and fallback categories. Some of this logic may migrate to the service layer (`services/transactions.py`) rather than provider logic.

### 🚫 Non-Exposed / Ancillary Functions

These functions contain logging and request validation scaffolding which may remain within the route or be restructured later:

- JSON input decoding
- request logging
- user_id propagation (unless centralized in middleware)

---

## ⏭ Next Steps

Proceed to evaluate the next exposed route: `teller_transactions.py`. After that, examine `__init__.py` and plan `services/transactions.py` and `providers/` creation.

Task log will now be updated with the function-level exposure map for this component.

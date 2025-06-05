# Tasklog: Exchange Token Refactor
by: Arch Linux Assistant
date: 2025-05-13
repo: pyNance

Checklist:
- [x] Refactor `generateLinkToken()` for dynamic products
- [x] Replace `/plaid/transactions/generate_link_token` with unified `/plaid/link_token`
- [x] Introduce `exchange_public_token_for_product()` in `helpers/plaid_exchange_helpers.py`
- [ ] Update frontend integration to use the new route

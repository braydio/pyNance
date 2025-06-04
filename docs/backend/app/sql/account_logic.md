# backend/app/sql/ Documentation

---

## 📘 `account_logic.py`

```markdown
# Account SQL Logic

## Purpose

Contains SQL-level helpers and routines related to the user account system. Primarily used for retrieving, verifying, or cross-referencing account IDs and metadata during data ingestion and reporting.

## Key Responsibilities

- Fetch account info by ID or external reference
- Resolve account ownership
- Validate active status and types

## Primary Functions

- `get_account_by_id(account_id)`

  - Simple ID lookup using raw SQL or query builder

- `get_accounts_for_user(user_id)`

  - Joins user context to account list, filters by active status

- `verify_account_ownership(user_id, account_id)`
  - Returns true/false if the user has rights to the account

## Inputs

- `account_id`, `user_id`
- (optional) `external_account_ref`, e.g., from Plaid or Teller

## Outputs

- Account row objects
- True/false results for validation

## Internal Dependencies

- `models.Account`
- `sqlalchemy`, `core.db_session`

## Known Behaviors

- Some lookups are case-insensitive for legacy support
- May preload balance or institution metadata via eager joins
- Failure cascades return `None`, not exception

## Related Docs

- [`docs/models/Account.md`](../../models/Account.md)
- [`docs/sql/AccountQueryPatterns.md`](../../sql/AccountQueryPatterns.md)
```

---

Ready for `category_logic.py`?

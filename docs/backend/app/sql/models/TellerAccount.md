# 📘 `TellerAccount` Model

```markdown
# TellerAccount Model

## Purpose

Extends `Account` to store Teller-specific metadata for linked financial institutions. Supports Teller API integrations for sync, webhook, and identification.

## Fields

- `id`: Primary key (UUID)
- `account_id`: FK to base `Account` table
- `teller_account_id`: External Teller account ID
- `institution_name`: Name of financial institution (e.g., "Chase")
- `institution_type`: Teller enum type (e.g., `depository`, `credit`)
- `access_token`: Teller-issued token (encrypted)
- `created_at`, `updated_at`: Audit fields

## Relationships

- Belongs to `Account`
- Implicitly tied to `User` through `account_id`

## Behaviors

- Auto-created during Teller sync webhook handling
- Used to lookup and refresh account metadata
- `access_token` is required for periodic balance updates

## Related Logic

- `sync_service.py` (Teller adapter)
- `account_logic.py`
- `plaid.py` & `teller.py` under `routes/`

## Related Docs

- [`docs/sync/teller_integration.md`](../../docs/sync/teller_integration.md)
- [`docs/models/Account.md`](../../docs/models/Account.md)
```

---

Would you like to continue with `AccountHistory` next?

## 📘 `Account` Model

```markdown
# Account Model

## Purpose

Represents a financial account belonging to a user. Each account can be linked to an external provider (Plaid, etc.) or be created manually. Used as a parent entity for transactions and balance data.

## Fields

- `id`: Primary key (UUID or autoincrement)
- `user_id`: Owner of the account
- `name`: Raw account name retained for edits/history compatibility (e.g., "Chase Checking")
- `display_name` (computed): Canonical UI label derived from `institution_name`, `subtype`/`type`, and optional masked suffix metadata when present in serializers
- `provider`: Source system (`plaid`, `manual`, etc.)
- `provider_account_id`: External reference ID
- `institution_name`: Bank or provider name
- `type`: Account type (`checking`, `savings`, `credit`, etc.)
- `current_balance`, `available_balance`: Live balance fields
- `currency`: ISO 4217 code (e.g. `USD`)
- `is_active`: Soft delete flag
- `created_at`, `updated_at`: Audit fields

## Relationships

- One-to-many with `Transaction`
- May have join with `BalanceSnapshot`

## Behaviors

- `is_synced`: True if provider != "manual"
- `display_name` formatter centralizes account labeling so API payloads can keep `name` stable while presenting consistent UI text
- Soft-deleted records are filtered from most queries
- Auto-sync flags used for webhook requery

## Related Logic

- [`account_logic.py`](../../backend/app/sql/account_logic.py)
- [`sync_service.py`](../../backend/app/services/sync_service.py)

## Related Docs

- [`docs/sql/AccountQueryPatterns.md`](../../docs/sql/AccountQueryPatterns.md)
- [`docs/dataflow/sync_jobs.md`](../../docs/dataflow/sync_jobs.md)
```

---

# 📘 `Transaction` Model

```markdown
# Transaction Model

## Purpose

Stores individual cash-flow events for a user account. Rows originate from Plaid
syncs or manual entries and power downstream balance calculations, budgeting, and
forecasting features.

## Fields

| Column                               | Type                          | Notes                                                                         |
| ------------------------------------ | ----------------------------- | ----------------------------------------------------------------------------- |
| `id`                                 | Integer (PK)                  | Auto-incrementing identifier used internally.                                 |
| `transaction_id`                     | String(64), unique, indexed   | Primary business key from Plaid or manual import; enforced unique constraint. |
| `user_id`                            | String(64), indexed, nullable | Owning user identifier for multi-tenant filtering.                            |
| `account_id`                         | String(64) FK                 | References `Account.account_id`; cascades on account deletion.                |
| `amount`                             | Numeric(18, 2)                | Stored as `Decimal`; preserves provider sign for inflow/outflow logic.        |
| `date`                               | DateTime(timezone=True)       | Timestamp of when the transaction occurred.                                   |
| `description`                        | String(256)                   | Raw provider description or user-supplied label.                              |
| `provider`                           | Enum[`manual`, `plaid`]       | Normalized via validator; defaults to `manual`.                               |
| `merchant_name`                      | String(128)                   | Resolved merchant display name (defaults to `"Unknown"`).                     |
| `merchant_type`                      | String(64)                    | Provider merchant type/category (defaults to `"Unknown"`).                    |
| `user_modified`                      | Boolean                       | Flagged when a human edits the transaction.                                   |
| `user_modified_fields`               | Text                          | Comma-separated/JSON list of manually edited attributes.                      |
| `updated_by_rule`                    | Boolean                       | Indicates a `TransactionRule` mutation applied during sync.                   |
| `category_id`                        | Integer FK, nullable          | Optional FK to `Category.id`; nullified on category deletion.                 |
| `category`                           | String(128)                   | Denormalized category label maintained beside `category_id`.                  |
| `category_slug`                      | String(128), indexed          | Canonical category key used for analytics grouping stability.                 |
| `category_display`                   | String(256)                   | Canonical UI label paired with `category_slug`.                               |
| `personal_finance_category`          | JSON                          | Raw Plaid personal finance category payload.                                  |
| `personal_finance_category_icon_url` | String                        | Icon URL associated with Plaid personal finance category.                     |
| `pending`                            | Boolean                       | True while Plaid reports the entry as unsettled.                              |
| `is_internal`                        | Boolean, indexed              | Marks internal transfers for reporting exclusions.                            |
| `internal_match_id`                  | String(64), nullable          | Stores counterpart `transaction_id` when `is_internal` is set.                |

## Relationships

- `plaid_meta`: One-to-one with `PlaidTransactionMeta` (cascade delete-orphan) for
  detailed Plaid metadata.
- `recurrence_rule`: Backref from `RecurringTransaction` when this row seeds a recurring
  pattern.

## Behaviors

- Plaid transaction syncs upsert the `plaid_meta` relationship via
  [`refresh_or_insert_plaid_metadata`](../../../../../backend/app/sql/refresh_metadata.py),
  ensuring Plaid metadata stays aligned with the base row.
- Internal transfer detection in
  [`account_logic.detect_internal_transfer`](../../../../../backend/app/sql/account_logic.py)
  flags matching debits/credits, toggling `is_internal` and wiring
  `internal_match_id` pairs to prevent double-counting balances.
- The provider validator keeps `provider` constrained to `manual`/`plaid`, defaulting
  to `manual` when unknown values arrive.
- Plaid ingestion paths persist canonical category metadata (`category_slug` and
  `category_display`) alongside the legacy/raw category payload for provenance.

## Related Logic

- [`transaction_models.py`](../../../../../backend/app/models/transaction_models.py)
- [`transactions_logic.md`](../transactions_logic.md)
- [`recurring_logic.md`](../recurring_logic.md)

## Related Docs

- [`transactions.md`](../../services/transactions.md)
- [`enhanced_account_history.md`](../../services/enhanced_account_history.md)
- [`sync_service.md`](../../services/sync_service.md)
```

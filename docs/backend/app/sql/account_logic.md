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
- (optional) `external_account_ref`, e.g., from Plaid

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

## Account serialization note

`get_accounts_from_db` and route payload builders now emit both `name` and `display_name`. `display_name` is the canonical UI label from `Account.display_name`, while `name` remains unchanged for compatibility-sensitive flows (edits/history).

## Merchant normalization

Both transaction ingestion paths use `app.utils.merchant_normalization.resolve_merchant` to enforce a shared fallback order (`merchant_name` -> `name` -> `description` -> `Unknown`). The helper strips common processor prefixes (for example `POS`, `SQ *`, and `PAYPAL *`), normalizes case/spacing, and emits a canonical `merchant_slug`. Ingestion preserves the raw source description in `Transaction.description` while persisting normalized merchant fields and metadata.

## Canonical category resolution contract

`get_or_create_category(primary, detailed, pfc_primary, pfc_detailed, pfc_icon_url)` now resolves categories by canonical slug first, then uses PFC and legacy paths as provenance fallbacks. The function persists:

- `Category.category_slug` (stable internal key)
- `Category.category_display` (UI label)
- Original Plaid category payload fields (`primary_category`, `detailed_category`, `pfc_*`)

Transaction upsert paths in this module persist canonical category fields on each transaction row (`category_slug`, `category_display`) in addition to the existing denormalized `category` string and raw `personal_finance_category` payload.

## Internal transfer classification policy

Internal transfer detection keeps amount/date matching as the baseline candidate filter (equal and opposite amount across different user accounts within the date tolerance), then applies shared heuristics to classify transfer intent and avoid spend-analytics false positives.

Classification behavior:

- Uses merchant/description keyword heuristics (`transfer`, `zelle`, `ach`, `wire`, and brokerage funding terms).
- Uses account context heuristics (`checking`, `savings`, `brokerage`) derived from account type/subtype/name.
- Rejects suspicious purchase-like pairs (`purchase`, `debit card`, `restaurant`, and related tokens) unless transfer signals are present.
- Writes explicit metadata to `Transaction.transfer_type` while preserving `Transaction.is_internal` for existing consumers.
- Exposes `internal_transfer_flag` as a compatibility alias for clients that prefer transfer-specific naming.

Spend analytics and summary endpoints continue to exclude rows where `is_internal` is true, so transfer classification metadata augments observability without changing existing exclusion filters.


## Investment scope normalization

`upsert_accounts` now accepts optional `enabled_products` scope data and persists explicit account flags:

- `is_investment`
- `investment_has_holdings`
- `investment_has_transactions`
- `product_provenance` (`product_scope`, `payload_type`, or `none`)

Account serialization (`get_accounts_from_db`) now emits these flags and a normalized `account_type` value. Investment-linked rows always serialize with `account_type = "investment"` even when upstream type values vary (for example `brokerage`).

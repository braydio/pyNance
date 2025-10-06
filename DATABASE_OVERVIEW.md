Overview

- ORM: Flask‑SQLAlchemy with Alembic migrations
- DB: Postgres target (SQLite supported in scripts)
- Monetary types: NUMERIC(18,2) (good), timestamps mixed Date/DateTime with/without tz
- Keys: Several tables use business keys (e.g., accounts.account_id string) as the main FK across the schema rather than the integer PK

Core Tables

- accounts (Projects/pyNance/backend/app/models/account_models.py:12)
  - Fields: integer id PK and string account_id unique, user_id, name, type, subtype, institution_name, institution_db_id FK to
    institutions, status, is_hidden, balance, link_type
  - Relations: One-to-one PlaidAccount, many Institution
- account_history (Projects/pyNance/backend/app/models/account_models.py:30)
  - Fields: account_id FK to accounts.account_id, user_id, date DateTime, balance, is_hidden
  - Unique: (account_id, date)
- financial_goals (Projects/pyNance/backend/app/models/account_models.py:48)
  - Fields: user_id, account_id FK, name, target_amount, due_date, notes
- Grouping/preferences (Projects/pyNance/backend/app/models/account_models.py:63,87,113)
  - account_groups (UUID string PK), account_group_memberships (join with unique (group_id, account_id)), account_group_preferences
    (per‑user active group)
  - account_snapshot_preferences stores selected account ids per user as JSON

Institutions

- institutions (Projects/pyNance/backend/app/models/institution_models.py:11)
  - Fields: name, provider, last_refreshed
  - Has many: accounts, plaid_accounts
- plaid_accounts (Projects/pyNance/backend/app/models/institution_models.py:26)
  - One‑to‑one with accounts.account_id, has Plaid-specific fields: access_token, item_id, product, plaid_institution_id,
    institution_db_id FK to institutions
- plaid_items, plaid_webhook_logs (Projects/pyNance/backend/app/models/institution_models.py:49,68)
  - plaid_items holds user_id, item_id unique, access_token, product, is_active, last_error
  - Webhook log stores payloads

Transactions & Categories

- categories (Projects/pyNance/backend/app/models/transaction_models.py:10)
  - Composite unique on (primary_category,detailed_category), optional parent self‑FK for hierarchy
- transactions (Projects/pyNance/backend/app/models/transaction_models.py:28)
  - Business key transaction_id unique, string FK target
  - Fields: user*id, account_id FK, amount NUMERIC, date DateTime(tz=True), description, provider, merchant*\*, pending, is_internal,
    internal_match_id, category_id FK, plus denormalized category string and PFC JSON/icon
- recurring_transactions (Projects/pyNance/backend/app/models/transaction_models.py:58)
  - FKs: transaction_id → transactions.transaction_id and account_id → accounts.account_id, schedule fields
- plaid_transaction_meta (Projects/pyNance/backend/app/models/transaction_models.py:86)
  - One‑to‑one with transactions.transaction_id, also FK to plaid_accounts.account_id, lots of Plaid detail JSON; unique on
    transaction_id

Investments

- securities, investment_holdings, investment_transactions (Projects/pyNance/backend/app/models/investment_models.py:9,23,44)
  - Holdings unique (account_id,security_id)
  - Investment tx primary key investment_transaction_id string, FKs to account/security

Planning

- planning_scenarios, planned_bills, scenario_allocations (UUID PKs) (Projects/pyNance/backend/app/models/planning_models.py:16,37,68)
  - Strong integrity via CheckConstraints and index patterns
  - ScenarioAllocation.kind Enum('fixed','percent'); constraints enforce value semantics

Relationships & On Delete

- Alembic sets ON DELETE rules (CASCADE/SET NULL) across FKs consistent with models (Projects/pyNance/backend/migrations/
  versions/8f2b541c2d5a_ondelete_rules.py:12)

Strengths

- Monetary values standardized to NUMERIC(18,2) (Projects/pyNance/backend/migrations/
  versions/4b9af1d3db6d_numeric_precision_and_utc_dates.py:14)
- Timestamps for transactions are timezone-aware; cascades and unique constraints are used appropriately
- Category hierarchy supported with self‑FK and composite uniqueness
- Planning domain has solid constraints and indices; holdings and group membership enforce uniqueness

Redundancies / Mixed Keys

- Dual keys on accounts: integer id and string account_id; most FKs reference account_id (string)
  - This adds complexity; either: make account_id the PK or use integer PK everywhere
- transactions has both category_id and category string (and Plaid PFC JSON). This risks drift between fields.
- accounts.institution_name duplicates data that is available via institutions relation (and Plaid/Teller linkages)
- plaid_accounts stores access_token and item_id while plaid_items also stores an access_token/item_id at item scope
  - This is likely redundant; a plaid_accounts.plaid_item_id FK would avoid duplicating tokens
- recurring_transactions stores both transaction_id and account_id
  - If the rule fundamentally derives from the transaction, account_id can be derived; if you want rules to outlive the source
    transaction, storing both still couples to that transaction’s id unnecessarily

Robustness / Integrity Gaps

- Mixed timestamp usage:
  - transactions.date is tz‑aware; others like account_history.date are naive DateTime (Projects/pyNance/backend/app/models/
    account_models.py:36)
  - Consider normalizing to Date-only for history, or tz-aware everywhere with a documented invariant
- Many domain enums stored as free text:
  - accounts.status, link_type, transactions.provider, account type/subtype, investment type/subtype
  - Enums or constrained domains would prevent invalid states
- user_id is a string across many tables with no FK to a users table
  - If multi-user is planned, missing referential integrity and cascade strategy; if single-user, nullable usage is okay but be
    explicit

Indexing Observations

- Present: indexes on most FKs and key columns (e.g., transactions.transaction_id unique, account_history unique composite, membership/
  order indices)
- Likely useful additions:
  - transactions: composite indexes for common queries: (account_id, date DESC), (user_id, date DESC), (category_id, date),
    (is_internal, date)
  - account_history: index on (account_id, date DESC) given time‑series access
  - plaid_transaction_meta.transaction_id already unique; OK
  - investment_transactions: (account_id, date DESC)

Concrete Improvements

- Standardize primary/foreign key strategy on accounts
  - Option A: make account_id the PK and drop integer id
  - Option B: make integer id the sole FK target, keep account_id as unique business key
  - Pick one and migrate references accordingly to simplify joins and constraints
- Normalize Plaid item/account linkage
  - Create plaid_account.plaid_item_id FK to plaid_items.id; remove access_token/item_id duplicates from plaid_accounts
  - Keep tokens at item scope; accounts inherit via the item relationship
- Reduce category duplication
  - Prefer category_id as the authoritative field; drop or make transactions.category a computed/cache field set by rules with a check
    that ensures coherence (or move to a view)
  - Consider deriving display fields from categories.computed_display_name (Projects/pyNance/backend/app/models/
    transaction_models.py:21)
- Constrain enums
  - Convert accounts.status, link_type, transactions.provider, account.type/subtype, investment.type/subtype to db enums or constrained
    text with checks
- Timestamp consistency
  - Make account_history.date a Date if it’s daily, or DateTime(timezone=True) and enforce UTC (document invariant); migrate existing
    values accordingly
- Recurring transactions decoupling
  - If rules should persist independently: remove the FK to transactions.transaction_id and store the needed pattern/fields +
    account_id
  - If you keep the FK, drop the redundant account_id to avoid drift
- Institution name denormalization
  - Remove or clearly label accounts.institution_name as denormalized; rely on the institutions table or add triggers/materialized view
    if needed in read paths
- Add missing indexes
  - transactions: (user_id, account_id, date DESC) as a composite or separate depending on query patterns
  - account_history: (account_id, date DESC)
- Multi‑tenant readiness
  - If multi-user: add a users table and FKs for user_id across tables plus cascade rules; add composite uniqueness where needed
    (user_id, account_id) to prevent cross‑user collisions

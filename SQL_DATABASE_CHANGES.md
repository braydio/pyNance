r models and usage, here are focused,
  high‑value refactors I’d recommend, ordered by impact.

  Data Types

  - Monetary precision: Replace Float with Numeric(18,2) (or store cents as
  Integer) for all money columns to eliminate rounding drift.
      - transactions.amount at backend/app/models/transaction_models.py:44
      - accounts.balance at backend/app/models/account_models.py:28
      - investment_holdings.quantity/cost_basis/institution_value at
  backend/app/models/investment_models.py:39, 40, 41
      - investment_transactions.amount/price/quantity/fees at backend/app/
  models/investment_models.py:67, 68, 69, 73
  - Datetime consistency: Your timestamps are timezone‑aware in the mixin,
  which is good. Ensure all date-like fields are semantically consistent:
      - transactions.date is DateTime but often used as a date in queries;
  consider either a computed date column (materialized) or consistently cast
  in queries and add indexes accordingly.

  Keys & Relations

  - Align FKs to internal numeric PKs: Several relations target business IDs
  (e.g., accounts.account_id string) instead of the surrogate accounts.id.
  For internal consistency/perf, add numeric FKs and migrate references
  gradually.
      - transactions.account_id -> accounts.account_id at backend/app/
  models/transaction_models.py:43
      - recurring_transactions.account_id at backend/app/models/
  transaction_models.py:85
      - plaid_accounts.account_id unique FK at backend/app/models/
  institution_models.py:33
      - Migration plan:
          - Add account_pk = db.Column(db.Integer,
  db.ForeignKey("accounts.id"), index=True, nullable=True) to dependent
  tables.
          - Backfill via join on accounts.account_id.
          - Switch queries to account_pk.
          - Make account_pk non‑null; keep account_id as a unique external
  key.
  - ON DELETE behavior: Explicitly set ondelete for FKs to avoid orphans and
  encode intent.
      - Example: Transaction.account_pk → ondelete="CASCADE" if you want to
  drop transactions with accounts (or SET NULL if you prefer retention).
  - Unify timestamp strategy: Planning models re‑declare created/updated
  columns; consider TimestampMixin for consistency unless you need distinct
  names (backend/app/models/planning_models.py:16).

  Indexes

  - Add practical composite indexes aligned to your hottest queries:
      - transactions (account_id, date DESC) for account history and charts.
      - transactions (user_id, date DESC) for user‑scoped listing.
      - transactions (category_id, date) for category filters.
      - account_history (account_id, date) already de facto, but ensure
  btree index exists beyond the unique constraint (backend/app/models/
  account_models.py:56).
      - If you keep using .filter(Transaction.is_internal...) in scans, add
  (is_internal, date) to accelerate those passes.
  - JSON usage in plaid_transaction_meta: If you filter on keys in category,
  location, etc., consider a GIN index later; otherwise defer.

  Normalization & Redundancy

  - Category duplication: Transaction has both category_id (FK) and a
  freeform category string (backend/app/models/transaction_models.py:53,
  54). Prefer the FK + join for truth; keep the string only if you need
  immutable snapshots from providers. If you keep both:
      - Rename the freeform to provider_category_label for clarity.
      - Backfill from Category where appropriate.
  - Institution duplication: Account.institution_name (backend/app/models/
  account_models.py:22) duplicates Account.institution relation. Prefer
  relation; consider deprecating the column after ensuring all UI paths use
  the relation.
  - User modeling: Many tables carry user_id strings without a users table
  FK. If multi‑user is a goal, add a users table with a surrogate key and
  migrate user_id to a proper FK (and indexes).
  - Provider access tokens at rest: PlaidAccount.access_token (backend/
  app/models/institution_models.py:41) and Teller tokens are stored
  as plaintext. Wrap with encryption at rest (KMS/Hashicorp/Vault) or
  application‑level envelope encryption; at minimum, restrict DB role access
  and audit.

  Data You Might Not Need

  - Transaction.category string if category_id is canonical and you don’t
  require provider‑verbatim history.
  - Account.institution_name if always resolvable via Institution relation.
  - Verbose Plaid raw payloads can be kept, but consider TTL, partitioning,
  or moving to object storage if size grows. Keep a slim subset in DB for
  auditing and re‑hydration.

  Missing/Useful Data

  - Currency on transactions: You store currency in
  PlaidTransactionMeta.iso_currency_code (backend/app/models/
  transaction_models.py:135) but not on Transaction. Add currency_code on
  transactions for manual/imported rows and consistent reporting.
  - Running balance per transaction (optional): If the UI often shows
  running balances, a computed and indexed running_balance snapshot can
  reduce server work, though your account_history service already covers
  much of this.
  - Merchant normalization: If you plan analytics by merchant, a merchants
  table keyed by normalized name/entity would help; backfill from
  merchant_entity_id (backend/app/models/transaction_models.py:138) where
  present.

  PostgreSQL Features To Leverage

  - True upserts: Use dialect_utils.dialect_insert + on_conflict_do_update
  for keys like transactions.transaction_id, accounts.account_id,
  securities.security_id, etc. This will simplify sync logic and the
  migration script.
  - Constraints:
      - CHECK (amount <> 0) if zeros shouldn’t exist.
      - CHECK (fees >= 0) on investment transactions.
  - Partitioning: If transactions grows into millions, consider time
  partitioning by month/quarter. Not urgent yet.

  Migration Plan (Incremental, Low Risk)

  - Add columns and indexes first (non‑breaking).
  - Backfill data in batches; validate counts.
  - Switch reads/writes to new columns in code.
  - Make new FKs non‑null; optionally drop deprecated columns later.
  - Add upsert paths where sync routines currently retry or skip on
  conflicts.

  If you want, I can draft concrete Alembic migrations for:

  - Monetary type changes with safe cast (Float → Numeric).
  - Adding transactions.currency_code, composite indexes, and account_pk
  FKs.
  - A helper data migration to backfill account_pk from account_id.

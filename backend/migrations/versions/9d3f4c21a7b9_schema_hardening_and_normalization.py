"""Schema hardening: accounts PK swap, enums, history date, plaid item FK, indexes.

Revision ID: 9d3f4c21a7b9
Revises: 8f2b541c2d5a
Create Date: 2025-10-06
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9d3f4c21a7b9"
# Merge both parallel heads to continue on a single lineage
down_revision = ("8f2b541c2d5a", "1f2a3b4c5d6e")
branch_labels = None
depends_on = None


account_status = sa.Enum(
    "active", "inactive", "closed", "archived", name="account_status"
)
# Remove legacy Teller variant from enum definitions; we only support Plaid/manual.
link_type = sa.Enum("manual", "plaid", name="link_type")
provider_type = sa.Enum("manual", "plaid", name="provider_type")


def upgrade() -> None:
    """Apply schema hardening changes for accounts, enums, and indexes."""
    bind = op.get_bind()
    dialect = bind.dialect.name
    inspector = sa.inspect(bind)

    # 1) accounts: ensure PK is on account_id, but only perform swap if needed
    pk = inspector.get_pk_constraint("accounts") or {}
    pk_cols = list(pk.get("constrained_columns") or [])
    cols = [c["name"] for c in inspector.get_columns("accounts")]

    if pk_cols and [c.lower() for c in pk_cols] != ["account_id"]:
        # Drop dependent FKs that reference accounts PK to allow PK modification
        fk_specs = [
            (
                "account_group_memberships",
                "account_group_memberships_account_id_fkey",
                {
                    "columns": ["account_id"],
                    "refcols": ["account_id"],
                    "ondelete": "CASCADE",
                },
            ),
            (
                "account_history",
                "account_history_account_id_fkey",
                {
                    "columns": ["account_id"],
                    "refcols": ["account_id"],
                    "ondelete": "CASCADE",
                },
            ),
            (
                "financial_goals",
                "financial_goals_account_id_fkey",
                {
                    "columns": ["account_id"],
                    "refcols": ["account_id"],
                    "ondelete": "CASCADE",
                },
            ),
            (
                "plaid_accounts",
                "plaid_accounts_account_id_fkey",
                {
                    "columns": ["account_id"],
                    "refcols": ["account_id"],
                    "ondelete": "CASCADE",
                },
            ),
            (
                "transactions",
                "transactions_account_id_fkey",
                {
                    "columns": ["account_id"],
                    "refcols": ["account_id"],
                    "ondelete": "CASCADE",
                },
            ),
            (
                "recurring_transactions",
                "recurring_transactions_account_id_fkey",
                {
                    "columns": ["account_id"],
                    "refcols": ["account_id"],
                    "ondelete": "CASCADE",
                },
            ),
            (
                "investment_holdings",
                "investment_holdings_account_id_fkey",
                {
                    "columns": ["account_id"],
                    "refcols": ["account_id"],
                    "ondelete": "CASCADE",
                },
            ),
            (
                "investment_transactions",
                "investment_transactions_account_id_fkey",
                {
                    "columns": ["account_id"],
                    "refcols": ["account_id"],
                    "ondelete": "CASCADE",
                },
            ),
        ]

        # Drop FKs
        for table, fk_name, _ in fk_specs:
            try:
                with op.batch_alter_table(table) as batch_op:
                    batch_op.drop_constraint(fk_name, type_="foreignkey")
            except Exception:
                pass

        # Swap PK to account_id and drop legacy id column if present
        with op.batch_alter_table("accounts") as batch_op:
            try:
                batch_op.drop_constraint("accounts_pkey", type_="primary")
            except Exception:
                pass
            batch_op.create_primary_key("accounts_pkey", ["account_id"])
            try:
                if "id" in cols:
                    batch_op.drop_column("id")
            except Exception:
                pass

        # Recreate FKs to reference accounts.account_id
        for table, fk_name, spec in fk_specs:
            try:
                with op.batch_alter_table(table) as batch_op:
                    batch_op.create_foreign_key(
                        fk_name,
                        "accounts",
                        spec["columns"],
                        spec["refcols"],
                        ondelete=spec.get("ondelete"),
                    )
            except Exception:
                pass
    else:
        # Already using account_id as PK; only ensure no stray legacy id column remains
        if "id" in cols:
            with op.batch_alter_table("accounts") as batch_op:
                try:
                    batch_op.drop_column("id")
                except Exception:
                    pass

    # 2) account_history.date -> Date (daily)
    if dialect == "postgresql":
        op.alter_column(
            "account_history",
            "date",
            type_=sa.Date(),
            existing_type=sa.DateTime(timezone=False),
            nullable=False,
            postgresql_using="date::date",
        )
    else:
        with op.batch_alter_table("account_history") as batch_op:
            batch_op.alter_column(
                "date", type_=sa.Date(), existing_type=sa.DateTime(), nullable=False
            )

    # 3) Create enums and alter columns with value normalization for Postgres
    if dialect == "postgresql":
        account_status.create(bind, checkfirst=True)
        link_type.create(bind, checkfirst=True)
        provider_type.create(bind, checkfirst=True)

        # Normalize existing values to valid labels using text casts only
        # Avoid casting to enum until after values are sanitized to prevent enum label errors
        # If column is already enum, cast back to enum on write to avoid type mismatch
        op.execute(
            "UPDATE accounts SET status = LOWER(status::text)::account_status WHERE status IS NOT NULL"
        )
        op.execute(
            "UPDATE accounts SET status = 'active'::account_status WHERE status IS NULL OR status::text NOT IN ('active','inactive','closed','archived')"
        )
        op.execute(
            "UPDATE accounts SET link_type = LOWER(link_type::text)::link_type WHERE link_type IS NOT NULL"
        )
        op.execute(
            "UPDATE accounts SET link_type = 'manual'::link_type WHERE link_type IS NULL OR link_type::text NOT IN ('manual','plaid')"
        )
        op.execute(
            "UPDATE transactions SET provider = LOWER(provider::text)::provider_type WHERE provider IS NOT NULL"
        )
        op.execute(
            "UPDATE transactions SET provider = 'manual'::provider_type WHERE provider IS NULL OR provider::text NOT IN ('manual','plaid')"
        )

        # Now alter column types using explicit USING casts and set defaults
        # Drop existing defaults first to avoid Postgres casting errors
        op.execute("ALTER TABLE accounts ALTER COLUMN status DROP DEFAULT")
        op.execute("ALTER TABLE accounts ALTER COLUMN link_type DROP DEFAULT")
        op.execute("ALTER TABLE transactions ALTER COLUMN provider DROP DEFAULT")

        op.execute(
            "ALTER TABLE accounts ALTER COLUMN status TYPE account_status USING status::account_status"
        )
        op.execute(
            "ALTER TABLE accounts ALTER COLUMN status SET DEFAULT 'active'::account_status"
        )
        op.execute(
            "ALTER TABLE accounts ALTER COLUMN link_type TYPE link_type USING link_type::link_type"
        )
        op.execute(
            "ALTER TABLE accounts ALTER COLUMN link_type SET DEFAULT 'manual'::link_type"
        )
        op.execute(
            "ALTER TABLE transactions ALTER COLUMN provider TYPE provider_type USING provider::provider_type"
        )
        op.execute(
            "ALTER TABLE transactions ALTER COLUMN provider SET DEFAULT 'manual'::provider_type"
        )
    else:
        with op.batch_alter_table("accounts") as batch_op:
            batch_op.alter_column(
                "status",
                type_=sa.String(length=64),
                existing_type=sa.String(length=64),
                existing_nullable=True,
                server_default=sa.text("'active'"),
            )
            batch_op.alter_column(
                "link_type",
                type_=sa.String(length=64),
                existing_type=sa.String(length=64),
                existing_nullable=True,
                server_default=sa.text("'manual'"),
            )
        with op.batch_alter_table("transactions") as batch_op:
            batch_op.alter_column(
                "provider",
                type_=sa.String(length=64),
                existing_type=sa.String(length=64),
                existing_nullable=True,
                server_default=sa.text("'manual'"),
            )

    # 4) plaid_accounts: add normalized plaid_item_id FK (idempotent)
    existing_pa_cols = [c["name"] for c in inspector.get_columns("plaid_accounts")]
    if "plaid_item_id" not in existing_pa_cols:
        with op.batch_alter_table("plaid_accounts") as batch_op:
            batch_op.add_column(sa.Column("plaid_item_id", sa.Integer(), nullable=True))
            try:
                batch_op.create_foreign_key(
                    "plaid_accounts_plaid_item_id_fkey",
                    "plaid_items",
                    ["plaid_item_id"],
                    ["id"],
                    ondelete="CASCADE",
                )
            except Exception:
                pass
            try:
                batch_op.create_index(
                    "ix_plaid_accounts_plaid_item_id", ["plaid_item_id"], unique=False
                )
            except Exception:
                pass

    # 5) Indexes for common query patterns
    op.create_index(
        "ix_transactions_account_date",
        "transactions",
        ["account_id", "date"],
    )
    op.create_index(
        "ix_transactions_user_date",
        "transactions",
        ["user_id", "date"],
    )
    op.create_index(
        "ix_transactions_category_date",
        "transactions",
        ["category_id", "date"],
    )
    op.create_index(
        "ix_account_history_account_date",
        "account_history",
        ["account_id", "date"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    # Drop indexes
    for name in [
        "ix_account_history_account_date",
        "ix_transactions_category_date",
        "ix_transactions_user_date",
        "ix_transactions_account_date",
    ]:
        try:
            op.drop_index(name)
        except Exception:
            pass

    # Remove plaid_item_id
    with op.batch_alter_table("plaid_accounts") as batch_op:
        try:
            batch_op.drop_index("ix_plaid_accounts_plaid_item_id")
        except Exception:
            pass
        try:
            batch_op.drop_constraint(
                "plaid_accounts_plaid_item_id_fkey", type_="foreignkey"
            )
        except Exception:
            pass
        try:
            batch_op.drop_column("plaid_item_id")
        except Exception:
            pass

    # Revert provider enum
    with op.batch_alter_table("transactions") as batch_op:
        batch_op.alter_column(
            "provider",
            type_=sa.String(length=64),
            existing_type=provider_type,
            existing_nullable=True,
        )

    # Revert accounts enums
    with op.batch_alter_table("accounts") as batch_op:
        batch_op.alter_column(
            "link_type",
            type_=sa.String(length=64),
            existing_type=link_type,
            existing_nullable=True,
        )
        batch_op.alter_column(
            "status",
            type_=sa.String(length=64),
            existing_type=account_status,
            existing_nullable=True,
        )

    # Revert account_history.date to DateTime (naive)
    if dialect == "postgresql":
        op.alter_column(
            "account_history",
            "date",
            type_=sa.DateTime(timezone=False),
            existing_type=sa.Date(),
            nullable=False,
            postgresql_using="date::timestamp",
        )
    else:
        with op.batch_alter_table("account_history") as batch_op:
            batch_op.alter_column(
                "date", type_=sa.DateTime(), existing_type=sa.Date(), nullable=False
            )

    # Restore accounts id column and PK if needed
    if dialect == "postgresql":
        with op.batch_alter_table("accounts") as batch_op:
            batch_op.add_column(sa.Column("id", sa.Integer(), nullable=True))
        op.execute("ALTER TABLE accounts DROP CONSTRAINT IF EXISTS accounts_pkey")
        op.execute("ALTER TABLE accounts ADD PRIMARY KEY (id)")
    else:
        with op.batch_alter_table("accounts") as batch_op:
            try:
                batch_op.drop_constraint("accounts_pkey", type_="primary")
            except Exception:
                pass
            batch_op.add_column(sa.Column("id", sa.Integer(), nullable=True))
            batch_op.create_primary_key("accounts_pkey", ["id"])

    # Drop enums
    if dialect == "postgresql":
        try:
            provider_type.drop(bind, checkfirst=True)
        except Exception:
            pass
        try:
            link_type.drop(bind, checkfirst=True)
        except Exception:
            pass
        try:
            account_status.drop(bind, checkfirst=True)
        except Exception:
            pass

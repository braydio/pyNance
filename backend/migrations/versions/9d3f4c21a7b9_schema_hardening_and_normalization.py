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
link_type = sa.Enum("manual", "plaid", "teller", name="link_type")
provider_type = sa.Enum("manual", "plaid", "teller", name="provider_type")


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    inspector = sa.inspect(bind)

    # 1) accounts: switch primary key to account_id and drop surrogate id
    with op.batch_alter_table("accounts") as batch_op:
        try:
            batch_op.drop_constraint("accounts_pkey", type_="primary")
        except Exception:
            pass
        batch_op.create_primary_key("accounts_pkey", ["account_id"])
        try:
            cols = [c["name"] for c in inspector.get_columns("accounts")]
            if "id" in cols:
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

        # Normalize existing string values to valid enum labels
        op.execute(
            "UPDATE accounts SET status = LOWER(status) WHERE status IS NOT NULL"
        )
        op.execute(
            "UPDATE accounts SET status = 'active' WHERE status IS NULL OR status NOT IN ('active','inactive','closed','archived')"
        )
        op.execute(
            "UPDATE accounts SET link_type = LOWER(link_type) WHERE link_type IS NOT NULL"
        )
        op.execute(
            "UPDATE accounts SET link_type = 'manual' WHERE link_type IS NULL OR link_type NOT IN ('manual','plaid','teller')"
        )
        op.execute(
            "UPDATE transactions SET provider = LOWER(provider) WHERE provider IS NOT NULL"
        )
        op.execute(
            "UPDATE transactions SET provider = 'manual' WHERE provider IS NULL OR provider NOT IN ('manual','plaid','teller')"
        )

        # Now alter column types using explicit USING casts and set defaults
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

    # 4) plaid_accounts: add normalized plaid_item_id FK
    with op.batch_alter_table("plaid_accounts") as batch_op:
        batch_op.add_column(sa.Column("plaid_item_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "plaid_accounts_plaid_item_id_fkey",
            "plaid_items",
            ["plaid_item_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_index(
            "ix_plaid_accounts_plaid_item_id", ["plaid_item_id"], unique=False
        )

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

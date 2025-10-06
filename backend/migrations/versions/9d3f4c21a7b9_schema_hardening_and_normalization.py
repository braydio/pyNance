"""Schema hardening: accounts PK swap, enums, history date, plaid item FK, indexes.

Revision ID: 9d3f4c21a7b9
Revises: 8f2b541c2d5a
Create Date: 2025-10-06
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9d3f4c21a7b9"
down_revision = "8f2b541c2d5a"
branch_labels = None
depends_on = None


account_status = sa.Enum("active", "inactive", "closed", "archived", name="account_status")
link_type = sa.Enum("manual", "plaid", "teller", name="link_type")
provider_type = sa.Enum("manual", "plaid", "teller", name="provider_type")


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    # 1) accounts: switch primary key to account_id and drop surrogate id
    if dialect == "postgresql":
        op.execute("ALTER TABLE accounts DROP CONSTRAINT IF EXISTS accounts_pkey")
        op.execute("ALTER TABLE accounts ADD PRIMARY KEY (account_id)")
        with op.batch_alter_table("accounts") as batch_op:
            # Drop integer id column if present
            cols = [c["name"] for c in bind.engine.execute(sa.text(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_name='accounts'
                """
            )).fetchall()]
            if "id" in cols:
                batch_op.drop_column("id")
    else:
        # Fallback using batch operations (SQLite)
        with op.batch_alter_table("accounts") as batch_op:
            try:
                batch_op.drop_constraint("accounts_pkey", type_="primary")
            except Exception:
                pass
            batch_op.create_primary_key("accounts_pkey", ["account_id"])
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
            batch_op.alter_column("date", type_=sa.Date(), existing_type=sa.DateTime(), nullable=False)

    # 3) Create enums and alter columns
    if dialect == "postgresql":
        account_status.create(bind, checkfirst=True)
        link_type.create(bind, checkfirst=True)
        provider_type.create(bind, checkfirst=True)

    with op.batch_alter_table("accounts") as batch_op:
        batch_op.alter_column(
            "status",
            type_=account_status,
            existing_type=sa.String(length=64),
            existing_nullable=True,
            server_default=sa.text("'active'"),
        )
        batch_op.alter_column(
            "link_type",
            type_=link_type,
            existing_type=sa.String(length=64),
            existing_nullable=True,
            server_default=sa.text("'manual'"),
        )

    with op.batch_alter_table("transactions") as batch_op:
        batch_op.alter_column(
            "provider",
            type_=provider_type,
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
        ["account_id", sa.text("date DESC")] if dialect == "postgresql" else ["account_id", "date"],
    )
    op.create_index(
        "ix_transactions_user_date",
        "transactions",
        ["user_id", sa.text("date DESC")] if dialect == "postgresql" else ["user_id", "date"],
    )
    op.create_index(
        "ix_transactions_category_date",
        "transactions",
        ["category_id", "date"],
    )
    op.create_index(
        "ix_account_history_account_date",
        "account_history",
        ["account_id", sa.text("date DESC")] if dialect == "postgresql" else ["account_id", "date"],
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
            batch_op.drop_constraint("plaid_accounts_plaid_item_id_fkey", type_="foreignkey")
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
            batch_op.alter_column("date", type_=sa.DateTime(), existing_type=sa.Date(), nullable=False)

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


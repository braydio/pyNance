"""Added metadata table

Revision ID: 3434a52b5364
Revises: e78654fb895b
Create Date: 2025-07-05 17:30:43.278456

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3434a52b5364"
down_revision = "e78654fb895b"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # Detect SQLite to avoid duplicate index errors (unique constraints auto-index in SQLite)
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"
    # Create index on accounts.account_id only for non-SQLite dialects
    if not is_sqlite:
        with op.batch_alter_table("accounts", schema=None) as batch_op:
            batch_op.create_index(
                batch_op.f("ix_accounts_account_id"), ["account_id"], unique=True
            )

    # Add metadata columns to categories if not already present
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing = {col["name"] for col in insp.get_columns("categories")}
    if "pfc_primary" not in existing:
        op.add_column(
            "categories", sa.Column("pfc_primary", sa.String(length=64), nullable=True)
        )
    if "pfc_detailed" not in existing:
        op.add_column(
            "categories", sa.Column("pfc_detailed", sa.String(length=64), nullable=True)
        )
    if "pfc_icon_url" not in existing:
        op.add_column(
            "categories",
            sa.Column("pfc_icon_url", sa.String(length=256), nullable=True),
        )

    # Create index on plaid_accounts.account_id if not already present
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing_ix = {ix["name"] for ix in insp.get_indexes("plaid_accounts")}
    if "ix_plaid_accounts_account_id" not in existing_ix:
        with op.batch_alter_table("plaid_accounts", schema=None) as batch_op:
            batch_op.create_index(
                batch_op.f("ix_plaid_accounts_account_id"), ["account_id"], unique=False
            )

    with op.batch_alter_table("transactions", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("personal_finance_category", sa.JSON(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("personal_finance_category_icon_url", sa.String(), nullable=True)
        )
        # Create index on transactions.transaction_id only for non-SQLite dialects
        if not is_sqlite:
            batch_op.create_index(
                batch_op.f("ix_transactions_transaction_id"),
                ["transaction_id"],
                unique=True,
            )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # Detect SQLite to avoid errors dropping auto-generated indexes
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"
    with op.batch_alter_table("transactions", schema=None) as batch_op:
        # Drop index on transactions.transaction_id only for non-SQLite dialects
        if not is_sqlite:
            batch_op.drop_index(batch_op.f("ix_transactions_transaction_id"))
        batch_op.drop_column("personal_finance_category_icon_url")
        batch_op.drop_column("personal_finance_category")

    with op.batch_alter_table("plaid_accounts", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_plaid_accounts_account_id"))

    with op.batch_alter_table("categories", schema=None) as batch_op:
        batch_op.drop_column("pfc_icon_url")
        batch_op.drop_column("pfc_detailed")
        batch_op.drop_column("pfc_primary")

    # Drop index on accounts.account_id only for non-SQLite dialects
    if not is_sqlite:
        with op.batch_alter_table("accounts", schema=None) as batch_op:
            batch_op.drop_index(batch_op.f("ix_accounts_account_id"))

    # ### end Alembic commands ###

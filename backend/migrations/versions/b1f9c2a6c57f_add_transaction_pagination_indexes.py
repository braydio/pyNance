"""Add composite indexes for transaction pagination filters and ordering.

Revision ID: b1f9c2a6c57f
Revises: f3d2c4a1b6e7
Create Date: 2025-12-18
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b1f9c2a6c57f"
down_revision = "f3d2c4a1b6e7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create composite indexes aligned to transaction pagination queries."""

    bind = op.get_bind()
    existing_indexes = {index["name"] for index in sa.inspect(bind).get_indexes("transactions")}

    if "ix_transactions_user_date_transaction_id_desc" not in existing_indexes:
        op.create_index(
            "ix_transactions_user_date_transaction_id_desc",
            "transactions",
            ["user_id", sa.text("date DESC"), sa.text("transaction_id DESC")],
            postgresql_using="btree",
        )
    if "ix_transactions_account_date_transaction_id_desc" not in existing_indexes:
        op.create_index(
            "ix_transactions_account_date_transaction_id_desc",
            "transactions",
            ["account_id", sa.text("date DESC"), sa.text("transaction_id DESC")],
            postgresql_using="btree",
        )
    if "ix_transactions_account_date" not in existing_indexes:
        op.create_index(
            "ix_transactions_account_date",
            "transactions",
            ["account_id", "date"],
            postgresql_using="btree",
        )


def downgrade() -> None:
    """Drop composite indexes tied to transaction pagination queries."""

    op.drop_index("ix_transactions_account_date", table_name="transactions")
    op.drop_index(
        "ix_transactions_account_date_transaction_id_desc", table_name="transactions"
    )
    op.drop_index(
        "ix_transactions_user_date_transaction_id_desc", table_name="transactions"
    )

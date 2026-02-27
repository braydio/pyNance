"""Add canonical merchant slug column to transactions.

Revision ID: a7c1d9e2f4b8
Revises: c2f8d9a4e1b7
Create Date: 2026-02-26 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a7c1d9e2f4b8"
down_revision = "c2f8d9a4e1b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add nullable merchant slug field used for canonical analytics grouping."""
    op.add_column(
        "transactions", sa.Column("merchant_slug", sa.String(length=128), nullable=True)
    )
    op.create_index(
        "ix_transactions_merchant_slug", "transactions", ["merchant_slug"], unique=False
    )


def downgrade() -> None:
    """Drop merchant slug field and index from transactions."""
    op.drop_index("ix_transactions_merchant_slug", table_name="transactions")
    op.drop_column("transactions", "merchant_slug")

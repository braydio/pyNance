"""Add transfer classification metadata to transactions.

Revision ID: d4a7b2e9c1f3
Revises: c2f8d9a4e1b7
Create Date: 2026-02-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d4a7b2e9c1f3"
down_revision = "c2f8d9a4e1b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "transactions",
        sa.Column("transfer_type", sa.String(length=32), nullable=True),
    )
    op.create_index(
        "ix_transactions_transfer_type",
        "transactions",
        ["transfer_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_transactions_transfer_type", table_name="transactions")
    op.drop_column("transactions", "transfer_type")

"""Add explicit investment account flags and provenance metadata.

Revision ID: e7b9f1c2a4d3
Revises: d4a7b2e9c1f3
Create Date: 2026-02-28
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e7b9f1c2a4d3"
down_revision = "d4a7b2e9c1f3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "accounts",
        sa.Column(
            "is_investment",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "accounts",
        sa.Column(
            "investment_has_holdings",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "accounts",
        sa.Column(
            "investment_has_transactions",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "accounts",
        sa.Column("product_provenance", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("accounts", "product_provenance")
    op.drop_column("accounts", "investment_has_transactions")
    op.drop_column("accounts", "investment_has_holdings")
    op.drop_column("accounts", "is_investment")

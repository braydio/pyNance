"""Create transaction_rules table.

Revision ID: c6e1f4b0d2a3
Revises: 7343a4630d46
Create Date: 2025-02-14 00:05:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c6e1f4b0d2a3"
down_revision = "7343a4630d46"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the transaction_rules table if it does not already exist."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("transaction_rules"):
        return

    op.create_table(
        "transaction_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.String(length=64), nullable=True),
        sa.Column("match_criteria", sa.JSON(), nullable=False),
        sa.Column("action", sa.JSON(), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.sql.expression.true(),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_transaction_rules_user_id",
        "transaction_rules",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the transaction_rules table and related indexes."""
    op.drop_index(
        "ix_transaction_rules_user_id",
        table_name="transaction_rules",
    )
    op.drop_table("transaction_rules")

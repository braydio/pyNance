"""Add Plaid sync cursor fields and webhook log table.

Revision ID: 7343a4630d46
Revises: 5af7f43f60ad
Create Date: 2025-02-14 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "7343a4630d46"
down_revision = "5af7f43f60ad"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add cursor tracking fields and create the webhook log table."""
    with op.batch_alter_table("plaid_accounts", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("sync_cursor", sa.String(length=256), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                "is_active",
                sa.Boolean(),
                server_default=sa.sql.expression.true(),
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("last_error", sa.Text(), nullable=True))

    op.create_table(
        "plaid_webhook_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_type", sa.String(length=128), nullable=True),
        sa.Column("webhook_type", sa.String(length=64), nullable=True),
        sa.Column("webhook_code", sa.String(length=64), nullable=True),
        sa.Column("item_id", sa.String(length=128), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Remove cursor fields and drop the webhook log table."""
    op.drop_table("plaid_webhook_logs")

    with op.batch_alter_table("plaid_accounts", schema=None) as batch_op:
        batch_op.drop_column("last_error")
        batch_op.drop_column("is_active")
        batch_op.drop_column("sync_cursor")

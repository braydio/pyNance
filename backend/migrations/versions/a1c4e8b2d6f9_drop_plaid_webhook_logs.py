"""Drop the unused plaid_webhook_logs table."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1c4e8b2d6f9"
down_revision = "c3e7f9a1d5b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Remove the webhook log table; Plaid webhooks are no longer handled."""

    inspector = sa.inspect(op.get_bind())
    if "plaid_webhook_logs" in inspector.get_table_names():
        op.drop_table("plaid_webhook_logs")


def downgrade() -> None:
    """Recreate the webhook log table."""

    op.create_table(
        "plaid_webhook_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=True),
        sa.Column("webhook_type", sa.String(length=64), nullable=True),
        sa.Column("webhook_code", sa.String(length=64), nullable=True),
        sa.Column("item_id", sa.String(length=128), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("received_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

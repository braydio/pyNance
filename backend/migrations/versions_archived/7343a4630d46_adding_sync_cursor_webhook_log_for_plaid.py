"""adding sync, cursor, webhook log for plaid

Revision ID: 7343a4630d46
Revises:
Create Date: 2025-05-25 02:51:24.506176
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "7343a4630d46"
down_revision = "72127368ea72"
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to plaid_accounts table
    op.add_column(
        "plaid_accounts",  # table name
        sa.Column("sync_cursor", sa.String(length=256), nullable=True),
    )
    op.add_column(
        "plaid_accounts",
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.sql.expression.true(),
            nullable=True,
        ),
    )
    op.add_column(
        "plaid_accounts",
        sa.Column("last_error", sa.Text(), nullable=True),
    )

    # Create plaid_webhook_logs table
    op.create_table(
        "plaid_webhook_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_type", sa.String(length=128), nullable=True),
        sa.Column("webhook_type", sa.String(length=64), nullable=True),
        sa.Column("webhook_code", sa.String(length=64), nullable=True),
        sa.Column("item_id", sa.String(length=128), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("received_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    # Drop plaid_webhook_logs table
    op.drop_table("plaid_webhook_logs")

    # Remove columns from plaid_accounts table
    op.drop_column("plaid_accounts", "last_error")
    op.drop_column("plaid_accounts", "is_active")
    op.drop_column("plaid_accounts", "sync_cursor")

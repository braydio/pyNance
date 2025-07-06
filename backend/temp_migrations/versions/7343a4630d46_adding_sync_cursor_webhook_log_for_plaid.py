"""adding sync, cursor, webhook log for plaid

Revision ID: 7343a4630d46
Revises:
Create Date: 2025-05-25 02:51:24.506176
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "7343a4630d46"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Update plaid_accounts table
    with op.batch_alter_table("plaid_accounts", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("sync_cursor", sa.String(length=256), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                "is_active",
                sa.Boolean(),
                server_default=sa.sql.expression.true(),
                nullable=True,
            )
        )
        batch_op.add_column(sa.Column("last_error", sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table("plaid_accounts", schema=None) as batch_op:
        batch_op.drop_column("last_error")
        batch_op.drop_column("is_active")
        batch_op.drop_column("sync_cursor")

    op.drop_table("plaid_webhook_logs")

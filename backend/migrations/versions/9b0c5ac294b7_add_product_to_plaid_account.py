"""Add product to PlaidAccount

Revision ID: 9b0c5ac294b7
Revises: 3434a52b5364
Create Date: 2025-07-07 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "9b0c5ac294b7"
down_revision = "3434a52b5364"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("plaid_accounts", schema=None) as batch_op:
        batch_op.add_column(sa.Column("product", sa.String(length=64), nullable=True))


def downgrade():
    with op.batch_alter_table("plaid_accounts", schema=None) as batch_op:
        batch_op.drop_column("product")

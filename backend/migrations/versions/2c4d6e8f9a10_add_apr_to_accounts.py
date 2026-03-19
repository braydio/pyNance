"""add apr to accounts

Revision ID: 2c4d6e8f9a10
Revises: 5f6a7b8c9d0e
Create Date: 2026-03-14 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2c4d6e8f9a10"
down_revision = "5f6a7b8c9d0e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("accounts", sa.Column("apr", sa.Numeric(precision=7, scale=4), nullable=True))


def downgrade():
    op.drop_column("accounts", "apr")

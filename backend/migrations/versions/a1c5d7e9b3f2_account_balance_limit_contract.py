"""account balance, limit and freshness contract

Revision ID: a1c5d7e9b3f2
Revises: f84c6e2a91b7
Create Date: 2026-10-14

"""

import sqlalchemy as sa
from alembic import op

revision = "a1c5d7e9b3f2"
down_revision = "f84c6e2a91b7"
branch_labels = None
depends_on = None

_COLUMNS = (
    ("credit_limit", sa.Numeric(18, 2)),
    ("available_balance", sa.Numeric(18, 2)),
    ("mask", sa.String(length=8)),
    ("currency_code", sa.String(length=8)),
    ("balance_as_of", sa.DateTime(timezone=True)),
)


def upgrade():
    inspector = sa.inspect(op.get_bind())
    existing = {column["name"] for column in inspector.get_columns("accounts")}
    for name, column_type in _COLUMNS:
        if name not in existing:
            op.add_column("accounts", sa.Column(name, column_type, nullable=True))


def downgrade():
    inspector = sa.inspect(op.get_bind())
    existing = {column["name"] for column in inspector.get_columns("accounts")}
    for name, _ in reversed(_COLUMNS):
        if name in existing:
            op.drop_column("accounts", name)

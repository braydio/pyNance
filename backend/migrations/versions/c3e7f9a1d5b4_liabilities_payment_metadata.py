"""plaid liabilities payment metadata

Revision ID: c3e7f9a1d5b4
Revises: b2d6e8f0c4a3
Create Date: 2026-10-14

"""

import sqlalchemy as sa
from alembic import op

revision = "c3e7f9a1d5b4"
down_revision = "b2d6e8f0c4a3"
branch_labels = None
depends_on = None

_COLUMNS = (
    ("minimum_payment_amount", sa.Numeric(18, 2)),
    ("next_payment_due_date", sa.Date()),
    ("statement_balance", sa.Numeric(18, 2)),
    ("statement_date", sa.Date()),
    ("liabilities_status", sa.String(length=24)),
    ("liabilities_as_of", sa.DateTime(timezone=True)),
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

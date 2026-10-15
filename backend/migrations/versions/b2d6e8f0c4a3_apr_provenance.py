"""apr provenance metadata

Revision ID: b2d6e8f0c4a3
Revises: a1c5d7e9b3f2
Create Date: 2026-10-14

"""

import sqlalchemy as sa
from alembic import op

revision = "b2d6e8f0c4a3"
down_revision = "a1c5d7e9b3f2"
branch_labels = None
depends_on = None

_COLUMNS = (
    ("apr_source", sa.String(length=32)),
    ("apr_as_of", sa.DateTime(timezone=True)),
    ("apr_confidence", sa.String(length=16)),
    ("apr_sample_cycles", sa.Integer()),
    ("apr_details", sa.JSON()),
)


def upgrade():
    inspector = sa.inspect(op.get_bind())
    existing = {column["name"] for column in inspector.get_columns("accounts")}
    for name, column_type in _COLUMNS:
        if name not in existing:
            op.add_column("accounts", sa.Column(name, column_type, nullable=True))
    # Rates stored before provenance existed were inferred from single interest charges
    # or entered without a record of origin; never present them as provider-reported.
    op.execute("UPDATE accounts SET apr_source = 'legacy_unverified' WHERE apr IS NOT NULL AND apr_source IS NULL")


def downgrade():
    inspector = sa.inspect(op.get_bind())
    existing = {column["name"] for column in inspector.get_columns("accounts")}
    for name, _ in reversed(_COLUMNS):
        if name in existing:
            op.drop_column("accounts", name)

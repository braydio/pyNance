"""store transaction dates as calendar dates

Revision ID: 7c1e9f4a2b6d
Revises: 6252a3a9e6a6
Create Date: 2026-07-16 04:15:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "7c1e9f4a2b6d"
down_revision = "6252a3a9e6a6"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # Existing values represent midnight UTC. Convert in UTC explicitly so
        # a session timezone west of UTC cannot shift them to the previous day.
        op.alter_column(
            "transactions",
            "date",
            existing_type=sa.DateTime(timezone=True),
            type_=sa.Date(),
            existing_nullable=False,
            postgresql_using="(date AT TIME ZONE 'UTC')::date",
        )
    else:
        with op.batch_alter_table("transactions") as batch_op:
            batch_op.alter_column(
                "date",
                existing_type=sa.DateTime(timezone=True),
                type_=sa.Date(),
                existing_nullable=False,
            )


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.alter_column(
            "transactions",
            "date",
            existing_type=sa.Date(),
            type_=sa.DateTime(timezone=True),
            existing_nullable=False,
            postgresql_using="date::timestamp AT TIME ZONE 'UTC'",
        )
    else:
        with op.batch_alter_table("transactions") as batch_op:
            batch_op.alter_column(
                "date",
                existing_type=sa.Date(),
                type_=sa.DateTime(timezone=True),
                existing_nullable=False,
            )

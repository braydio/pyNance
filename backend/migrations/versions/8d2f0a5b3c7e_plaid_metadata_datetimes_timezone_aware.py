"""make Plaid metadata datetimes timezone aware

Revision ID: 8d2f0a5b3c7e
Revises: 7c1e9f4a2b6d
Create Date: 2026-07-16 04:25:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "8d2f0a5b3c7e"
down_revision = "7c1e9f4a2b6d"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # Prefer the original Plaid ISO-8601 values retained in raw JSON so
        # their offsets determine the exact instant. The fallback reflects how
        # legacy naive values were stored by the America/New_York deployment.
        op.alter_column(
            "plaid_transaction_meta",
            "datetime",
            existing_type=sa.DateTime(timezone=False),
            type_=sa.DateTime(timezone=True),
            existing_nullable=True,
            postgresql_using=(
                "CASE WHEN raw->>'datetime' IS NOT NULL "
                "THEN (raw->>'datetime')::timestamptz "
                "ELSE datetime AT TIME ZONE 'America/New_York' END"
            ),
        )
        op.alter_column(
            "plaid_transaction_meta",
            "authorized_datetime",
            existing_type=sa.DateTime(timezone=False),
            type_=sa.DateTime(timezone=True),
            existing_nullable=True,
            postgresql_using=(
                "CASE WHEN raw->>'authorized_datetime' IS NOT NULL "
                "THEN (raw->>'authorized_datetime')::timestamptz "
                "ELSE authorized_datetime AT TIME ZONE 'America/New_York' END"
            ),
        )
    else:
        with op.batch_alter_table("plaid_transaction_meta") as batch_op:
            batch_op.alter_column(
                "datetime",
                existing_type=sa.DateTime(timezone=False),
                type_=sa.DateTime(timezone=True),
                existing_nullable=True,
            )
            batch_op.alter_column(
                "authorized_datetime",
                existing_type=sa.DateTime(timezone=False),
                type_=sa.DateTime(timezone=True),
                existing_nullable=True,
            )


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for column_name in ("datetime", "authorized_datetime"):
            op.alter_column(
                "plaid_transaction_meta",
                column_name,
                existing_type=sa.DateTime(timezone=True),
                type_=sa.DateTime(timezone=False),
                existing_nullable=True,
                postgresql_using=f"{column_name} AT TIME ZONE 'America/New_York'",
            )
    else:
        with op.batch_alter_table("plaid_transaction_meta") as batch_op:
            for column_name in ("datetime", "authorized_datetime"):
                batch_op.alter_column(
                    column_name,
                    existing_type=sa.DateTime(timezone=True),
                    type_=sa.DateTime(timezone=False),
                    existing_nullable=True,
                )

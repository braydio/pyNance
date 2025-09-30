"""Add account snapshot preferences table

Revision ID: d1f3c4b5a6e7
Revises: 7d392159f553
Create Date: 2024-07-15 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d1f3c4b5a6e7"
down_revision = "7d392159f553"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if not insp.has_table("account_snapshot_preferences"):
        op.create_table(
            "account_snapshot_preferences",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.String(length=64), nullable=False),
            sa.Column("selected_account_ids", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", name="uq_account_snapshot_preferences_user"),
        )
        insp = sa.inspect(bind)

    indexes = {idx["name"] for idx in insp.get_indexes("account_snapshot_preferences")}
    if "ix_account_snapshot_preferences_user_id" not in indexes:
        op.create_index(
            "ix_account_snapshot_preferences_user_id",
            "account_snapshot_preferences",
            ["user_id"],
        )


def downgrade():
    op.drop_index(
        "ix_account_snapshot_preferences_user_id",
        table_name="account_snapshot_preferences",
    )
    op.drop_table("account_snapshot_preferences")

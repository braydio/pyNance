"""Create account group tables for dashboard preferences."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8d3f3e3e8e8d"
down_revision = "768e5d55d4c4"
branch_labels = None
depends_on = None


def upgrade():
    """Create tables to persist account groups and memberships."""
    op.create_table(
        "account_groups",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column(
            "name", sa.String(length=128), nullable=False, server_default="Group"
        ),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accent", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_account_groups_user_id",
        "account_groups",
        ["user_id"],
    )
    op.create_index(
        "ix_account_groups_position",
        "account_groups",
        ["position"],
    )

    op.create_table(
        "account_group_memberships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.String(length=36), nullable=False),
        sa.Column("account_id", sa.String(length=64), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["group_id"], ["account_groups.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["account_id"], ["accounts.account_id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "group_id", "account_id", name="uq_account_group_membership"
        ),
    )
    op.create_index(
        "ix_account_group_memberships_group_id",
        "account_group_memberships",
        ["group_id"],
    )
    op.create_index(
        "ix_account_group_memberships_account_id",
        "account_group_memberships",
        ["account_id"],
    )

    op.create_table(
        "account_group_preferences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.String(length=64), nullable=False, unique=True),
        sa.Column("active_group_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["active_group_id"], ["account_groups.id"], ondelete="SET NULL"
        ),
    )
    op.create_index(
        "ix_account_group_preferences_user_id",
        "account_group_preferences",
        ["user_id"],
        unique=True,
    )
    op.create_index(
        "ix_account_group_preferences_active_group_id",
        "account_group_preferences",
        ["active_group_id"],
    )


def downgrade():
    """Drop account group tables."""
    op.drop_index(
        "ix_account_group_preferences_active_group_id",
        table_name="account_group_preferences",
    )
    op.drop_index(
        "ix_account_group_preferences_user_id",
        table_name="account_group_preferences",
    )
    op.drop_table("account_group_preferences")

    op.drop_index(
        "ix_account_group_memberships_account_id",
        table_name="account_group_memberships",
    )
    op.drop_index(
        "ix_account_group_memberships_group_id",
        table_name="account_group_memberships",
    )
    op.drop_table("account_group_memberships")

    op.drop_index(
        "ix_account_groups_position",
        table_name="account_groups",
    )
    op.drop_index(
        "ix_account_groups_user_id",
        table_name="account_groups",
    )
    op.drop_table("account_groups")

"""Create account_snapshot_preferences table."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5af7f43f60ad"
down_revision = "9b0c5ac294b7"
branch_labels = None
depends_on = None


def upgrade():
    """Create the account_snapshot_preferences table."""
    op.create_table(
        "account_snapshot_preferences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.String(length=64), nullable=False, unique=True),
        sa.Column("selected_account_ids", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_account_snapshot_preferences_user_id",
        "account_snapshot_preferences",
        ["user_id"],
        unique=True,
    )


def downgrade():
    """Drop the account_snapshot_preferences table and related indexes."""
    op.drop_index(
        "ix_account_snapshot_preferences_user_id",
        table_name="account_snapshot_preferences",
    )
    op.drop_table("account_snapshot_preferences")

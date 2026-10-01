"""add persistent LLM settings

Revision ID: a3c8e1f4b2d7
Revises: 8d2f0a5b3c7e
Create Date: 2026-08-03 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "a3c8e1f4b2d7"
down_revision = "8d2f0a5b3c7e"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "llm_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("custom_message_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("base_url", sa.String(length=2048), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("llm_settings")

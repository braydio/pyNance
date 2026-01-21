"""Add tags and transaction_tags tables for transaction labeling.

Revision ID: 55d16a2ff3e7
Revises: b1f9c2a6c57f
Create Date: 2026-02-17
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "55d16a2ff3e7"
down_revision = "b1f9c2a6c57f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create tag tables and association indexes."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "tags" not in existing_tables:
        op.create_table(
            "tags",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.String(length=64), nullable=False),
            sa.Column("name", sa.String(length=64), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.UniqueConstraint("user_id", "name", name="uq_tags_user_name"),
        )
    existing_tag_indexes = {idx["name"] for idx in inspector.get_indexes("tags")}
    if "ix_tags_user_id" not in existing_tag_indexes:
        op.create_index("ix_tags_user_id", "tags", ["user_id"])

    if "transaction_tags" not in existing_tables:
        op.create_table(
            "transaction_tags",
            sa.Column(
                "transaction_id",
                sa.String(length=64),
                sa.ForeignKey("transactions.transaction_id", ondelete="CASCADE"),
                primary_key=True,
            ),
            sa.Column(
                "tag_id",
                sa.Integer(),
                sa.ForeignKey("tags.id", ondelete="CASCADE"),
                primary_key=True,
            ),
        )
    existing_tt_indexes = {idx["name"] for idx in inspector.get_indexes("transaction_tags")}
    if "ix_transaction_tags_transaction_id" not in existing_tt_indexes:
        op.create_index(
            "ix_transaction_tags_transaction_id",
            "transaction_tags",
            ["transaction_id"],
        )
    if "ix_transaction_tags_tag_id" not in existing_tt_indexes:
        op.create_index(
            "ix_transaction_tags_tag_id",
            "transaction_tags",
            ["tag_id"],
        )


def downgrade() -> None:
    """Drop tag tables and association indexes."""

    op.drop_index(
        "ix_transaction_tags_tag_id",
        table_name="transaction_tags",
    )
    op.drop_index(
        "ix_transaction_tags_transaction_id",
        table_name="transaction_tags",
    )
    op.drop_table("transaction_tags")
    op.drop_index("ix_tags_user_id", table_name="tags")
    op.drop_table("tags")

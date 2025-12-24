"""legacy models.py move

Revision ID: f71197d4f032
Revises: 18acdf1fa2ca
Create Date: 2025-08-19 22:56:44.581838

This migration is a no-op.
Alembic autogen incorrectly detected NUMERIC → UUID changes
due to SQLite type reflection. In reality, UUIDs were already in use.
"""


# revision identifiers, used by Alembic.
revision = "f71197d4f032"
down_revision = "18acdf1fa2ca"
branch_labels = None
depends_on = None


def upgrade():
    # No schema changes required
    pass


def downgrade():
    # No schema changes to revert
    pass

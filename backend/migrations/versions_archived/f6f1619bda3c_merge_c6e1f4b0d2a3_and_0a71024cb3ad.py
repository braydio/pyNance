"""Merge heads c6e1f4b0d2a3 and 0a71024cb3ad.

Revision ID: f6f1619bda3c
Revises: c6e1f4b0d2a3, 0a71024cb3ad
Create Date: 2025-09-22 22:10:00.000000
"""

# revision identifiers, used by Alembic.
revision = "f6f1619bda3c"
down_revision = ("c6e1f4b0d2a3", "0a71024cb3ad")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """No schema changes; consolidates divergent heads."""
    pass


def downgrade() -> None:
    """No-op downgrade for merge revision."""
    pass

"""Baseline PostgreSQL schema created from the current SQLAlchemy models."""

from alembic import op
from flask import current_app


# revision identifiers, used by Alembic.
revision = 'cc9e65c88885'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    metadata = current_app.extensions["migrate"].db.metadata
    metadata.create_all(bind=bind)


def downgrade():
    bind = op.get_bind()
    metadata = current_app.extensions["migrate"].db.metadata
    metadata.drop_all(bind=bind)

"""Add recurring_streams.candidate_key for idempotent detector upserts.

``candidate_key`` is a deterministic SHA-256 of the detector's stream identity. It is NULL for
manual and legacy streams, and unique per user when present, so a rescan can never create a second
copy of the same candidate.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c4f8a1d3e5b7"
down_revision = "b7d2e4f6a8c1"
branch_labels = None
depends_on = None

CONSTRAINT = "uq_recurring_streams_user_candidate"


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("recurring_streams")}
    uniques = {u["name"] for u in inspector.get_unique_constraints("recurring_streams")}
    with op.batch_alter_table("recurring_streams") as batch:
        if "candidate_key" not in columns:
            batch.add_column(sa.Column("candidate_key", sa.String(64), nullable=True))
        if CONSTRAINT not in uniques:
            batch.create_unique_constraint(CONSTRAINT, ["user_id", "candidate_key"])


def downgrade() -> None:
    with op.batch_alter_table("recurring_streams") as batch:
        batch.drop_constraint(CONSTRAINT, type_="unique")
        batch.drop_column("candidate_key")

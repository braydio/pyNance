"""Preserve Plaid source history and make category identity canonical.

Revision ID: e6a9c2f4b8d1
Revises: a3c8e1f4b2d7
"""

import sqlalchemy as sa
from alembic import op

revision = "e6a9c2f4b8d1"
down_revision = "a3c8e1f4b2d7"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("categories") as batch:
        batch.drop_constraint("uq_category_composite", type_="unique")
    op.create_table(
        "plaid_source_events",
        sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), primary_key=True),
        sa.Column("run_id", sa.String(64), nullable=False),
        sa.Column("page_index", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("transaction_id", sa.String(64), nullable=False),
        sa.Column("account_id", sa.String(64)),
        sa.Column("item_id", sa.String(64)),
        sa.Column("endpoint", sa.String(64), nullable=False),
        sa.Column("request_id", sa.String(128)),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("payload_sha256", sa.String(64), nullable=False),
        sa.Column("cursor_before", sa.Text()),
        sa.Column("cursor_after", sa.Text()),
        sa.UniqueConstraint("run_id", "page_index", "event_type", "transaction_id", name="uq_plaid_source_event"),
    )
    op.create_index("ix_plaid_source_events_transaction_id", "plaid_source_events", ["transaction_id"])
    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            """CREATE FUNCTION reject_plaid_source_event_mutation() RETURNS trigger
            LANGUAGE plpgsql AS $$ BEGIN
                RAISE EXCEPTION 'Plaid source events are append-only';
            END $$"""
        )
        op.execute(
            """CREATE TRIGGER plaid_source_events_immutable BEFORE UPDATE OR DELETE
            ON plaid_source_events FOR EACH ROW EXECUTE FUNCTION reject_plaid_source_event_mutation()"""
        )
        op.execute(
            """CREATE TRIGGER plaid_source_events_no_truncate BEFORE TRUNCATE
            ON plaid_source_events FOR EACH STATEMENT EXECUTE FUNCTION reject_plaid_source_event_mutation()"""
        )


def downgrade():
    # Never silently discard audit evidence or merge incompatible categories.
    raise RuntimeError("Restore a verified backup to reverse this audit-preserving migration")

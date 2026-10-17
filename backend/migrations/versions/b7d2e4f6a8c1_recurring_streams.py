"""Add recurring_streams and recurring_stream_evidence; copy valid legacy recurring rows.

The legacy ``recurring_transactions`` table is left untouched. Valid rows are copied as
``source='legacy'`` streams; orphaned, ownerless, unknown-cadence or unknown-sign rows are skipped
and counted in the migration log instead of being guessed at.
"""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b7d2e4f6a8c1"
down_revision = "a1c4e8b2d6f9"
branch_labels = None
depends_on = None

logger = logging.getLogger("alembic.runtime.migration")

_LEGACY_NAMESPACE = uuid.UUID("5c1a2b6e-3f7d-4c58-9a10-2f6b8d4e7a31")
_CADENCES = {
    "once": "once",
    "weekly": "weekly",
    "biweekly": "biweekly",
    "bi-weekly": "biweekly",
    "every_two_weeks": "biweekly",
    "semimonthly": "semimonthly",
    "monthly": "monthly",
    "quarterly": "quarterly",
    "yearly": "yearly",
    "annual": "yearly",
    "annually": "yearly",
}


def _copy_legacy_rows(bind) -> dict:
    """Copy valid legacy rows into ``recurring_streams`` (idempotent) and return counters."""
    counters = {"copied": 0, "already_present": 0, "skipped_orphan": 0, "skipped_no_owner": 0}
    counters.update({"skipped_cadence": 0, "skipped_sign_unknown": 0})
    inspector = sa.inspect(bind)
    if "recurring_transactions" not in inspector.get_table_names():
        return counters

    rows = bind.execute(
        sa.text(
            "SELECT r.id AS rid, r.account_id AS account_id, r.frequency AS frequency, "
            "r.next_due_date AS next_due_date, r.notes AS notes, "
            "t.transaction_id AS tx_id, t.amount AS amount, t.provider AS provider, "
            "t.description AS description, t.merchant_name AS merchant_name, "
            "a.user_id AS user_id "
            "FROM recurring_transactions r "
            "LEFT JOIN transactions t ON t.transaction_id = r.transaction_id "
            "LEFT JOIN accounts a ON a.account_id = r.account_id"
        )
    ).mappings()
    streams = sa.table(
        "recurring_streams",
        sa.column("id", sa.String),
        sa.column("user_id", sa.String),
        sa.column("account_id", sa.String),
        sa.column("merchant_key", sa.String),
        sa.column("display_name", sa.String),
        sa.column("amount_cash_delta", sa.Numeric),
        sa.column("amount_mode", sa.String),
        sa.column("cadence", sa.String),
        sa.column("anchor_date", sa.Date),
        sa.column("status", sa.String),
        sa.column("source", sa.String),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
        sa.column("confirmed_at", sa.DateTime(timezone=True)),
        sa.column("notes", sa.Text),
    )
    now = datetime.now(timezone.utc)
    for row in rows:
        if row["tx_id"] is None:
            counters["skipped_orphan"] += 1
            continue
        if not row["user_id"]:
            counters["skipped_no_owner"] += 1
            continue
        cadence = _CADENCES.get(str(row["frequency"] or "").strip().lower())
        if cadence is None or row["next_due_date"] is None:
            counters["skipped_cadence"] += 1
            continue
        if str(row["provider"] or "").lower() != "plaid":
            counters["skipped_sign_unknown"] += 1  # manual rows carry no direction
            continue
        anchor = row["next_due_date"]
        if not isinstance(anchor, date):  # raw SQL on SQLite returns ISO strings
            anchor = date.fromisoformat(str(anchor)[:10])
        stream_id = str(uuid.uuid5(_LEGACY_NAMESPACE, f"legacy:{row['rid']}"))
        if bind.execute(sa.text("SELECT 1 FROM recurring_streams WHERE id = :i"), {"i": stream_id}).first():
            counters["already_present"] += 1
            continue
        name = (row["merchant_name"] if row["merchant_name"] not in (None, "", "Unknown") else None) or row[
            "description"
        ]
        bind.execute(
            streams.insert().values(
                id=stream_id,
                user_id=row["user_id"],
                account_id=row["account_id"],
                merchant_key=(str(name).strip().lower()[:160] if name else None),
                display_name=str(name or "Recurring payment")[:256],
                amount_cash_delta=-Decimal(str(row["amount"])),
                amount_mode="fixed",
                cadence=cadence,
                anchor_date=anchor,
                status="confirmed",
                source="legacy",
                created_at=now,
                updated_at=now,
                confirmed_at=now,
                notes=row["notes"],
            )
        )
        counters["copied"] += 1
    return counters


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())

    if "recurring_streams" not in existing:
        op.create_table(
            "recurring_streams",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("user_id", sa.String(64), nullable=False),
            sa.Column(
                "account_id",
                sa.String(64),
                sa.ForeignKey("accounts.account_id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("merchant_key", sa.String(160), nullable=True),
            sa.Column("display_name", sa.String(256), nullable=False),
            sa.Column("amount_cash_delta", sa.Numeric(18, 2), nullable=False),
            sa.Column("amount_mode", sa.String(16), nullable=False),
            sa.Column("cadence", sa.String(20), nullable=False),
            sa.Column("anchor_date", sa.Date, nullable=False),
            sa.Column("status", sa.String(16), nullable=False),
            sa.Column("source", sa.String(16), nullable=False),
            sa.Column("confidence", sa.Numeric(4, 3), nullable=True),
            sa.Column("last_observed", sa.Date, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("notes", sa.Text, nullable=True),
            sa.CheckConstraint("amount_mode IN ('fixed', 'variable')", name="ck_recurring_streams_amount_mode"),
            sa.CheckConstraint(
                "cadence IN ('once', 'weekly', 'biweekly', 'semimonthly', 'monthly', 'quarterly', 'yearly')",
                name="ck_recurring_streams_cadence",
            ),
            sa.CheckConstraint(
                "status IN ('proposed', 'confirmed', 'ignored', 'ended')", name="ck_recurring_streams_status"
            ),
            sa.CheckConstraint("source IN ('manual', 'detected', 'legacy')", name="ck_recurring_streams_source"),
        )
        op.create_index("ix_recurring_streams_account_id", "recurring_streams", ["account_id"])
        op.create_index(
            "ix_recurring_streams_user_status_anchor", "recurring_streams", ["user_id", "status", "anchor_date"]
        )
        op.create_index(
            "ix_recurring_streams_user_account_merchant",
            "recurring_streams",
            ["user_id", "account_id", "merchant_key"],
        )

    if "recurring_stream_evidence" not in existing:
        op.create_table(
            "recurring_stream_evidence",
            sa.Column("id", sa.BigInteger().with_variant(sa.Integer, "sqlite"), primary_key=True, autoincrement=True),
            sa.Column(
                "stream_id",
                sa.String(36),
                sa.ForeignKey("recurring_streams.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("transaction_id", sa.String(64), nullable=True),
            sa.Column("observed_at", sa.Date, nullable=False),
            sa.Column("raw_amount", sa.Numeric(18, 2), nullable=True),
            sa.Column("canonical_amount", sa.Numeric(18, 2), nullable=True),
            sa.Column("merchant_key", sa.String(160), nullable=True),
            sa.Column("decision", sa.String(24), nullable=False),
            sa.Column("reason", sa.JSON, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("stream_id", "transaction_id", name="uq_recurring_stream_evidence_stream_tx"),
        )
        op.create_index("ix_recurring_stream_evidence_stream_id", "recurring_stream_evidence", ["stream_id"])

    counters = _copy_legacy_rows(bind)
    logger.info("recurring_streams legacy copy: %s", counters)


def downgrade() -> None:
    """Drop the new tables only; the legacy ``recurring_transactions`` table was never modified."""
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "recurring_stream_evidence" in tables:
        op.drop_table("recurring_stream_evidence")
    if "recurring_streams" in tables:
        op.drop_table("recurring_streams")

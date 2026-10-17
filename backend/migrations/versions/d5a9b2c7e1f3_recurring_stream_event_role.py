"""Add recurring_streams.event_role / funding_account_id / destination_account_id.

``event_role`` says how a stream behaves in the forecast ledger. ``liability_payment`` streams move
cash from ``funding_account_id`` to the liability ``destination_account_id`` (a card or loan).
Every other role keeps the existing behaviour, so all current rows default to ``ordinary_expense``.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d5a9b2c7e1f3"
down_revision = "c4f8a1d3e5b7"
branch_labels = None
depends_on = None

ROLE_CHECK = "ck_recurring_streams_event_role"
ROLES = "('ordinary_expense', 'income', 'liability_payment', 'transfer')"


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("recurring_streams")}
    checks = {c["name"] for c in inspector.get_check_constraints("recurring_streams")}
    foreign_keys = {fk["name"] for fk in inspector.get_foreign_keys("recurring_streams")}
    with op.batch_alter_table("recurring_streams") as batch:
        if "event_role" not in columns:
            batch.add_column(sa.Column("event_role", sa.String(24), nullable=False, server_default="ordinary_expense"))
        if "funding_account_id" not in columns:
            batch.add_column(sa.Column("funding_account_id", sa.String(64), nullable=True))
        if "destination_account_id" not in columns:
            batch.add_column(sa.Column("destination_account_id", sa.String(64), nullable=True))
        if ROLE_CHECK not in checks:
            batch.create_check_constraint(ROLE_CHECK, f"event_role IN {ROLES}")
        for name, column in (
            ("fk_recurring_streams_funding_account", "funding_account_id"),
            ("fk_recurring_streams_destination_account", "destination_account_id"),
        ):
            if name not in foreign_keys:
                batch.create_foreign_key(name, "accounts", [column], ["account_id"], ondelete="SET NULL")


def downgrade() -> None:
    with op.batch_alter_table("recurring_streams") as batch:
        batch.drop_constraint("fk_recurring_streams_destination_account", type_="foreignkey")
        batch.drop_constraint("fk_recurring_streams_funding_account", type_="foreignkey")
        batch.drop_constraint(ROLE_CHECK, type_="check")
        batch.drop_column("destination_account_id")
        batch.drop_column("funding_account_id")
        batch.drop_column("event_role")

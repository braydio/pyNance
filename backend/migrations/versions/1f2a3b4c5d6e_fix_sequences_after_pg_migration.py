"""Align sequences with current max IDs after data migration.

This fixes duplicate key errors like:
  psycopg.errors.UniqueViolation: duplicate key value violates unique constraint "transactions_pkey"

by setting the underlying sequences to max(id) for affected tables.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "1f2a3b4c5d6e"
down_revision = "4b9af1d3db6d"
branch_labels = None
depends_on = None


def _reset_sequence(table: str, pk: str = "id") -> None:
    # Use pg_get_serial_sequence to resolve the sequence name and set it to max(pk)
    op.execute(
        f"""
        SELECT setval(
            pg_get_serial_sequence('{table}', '{pk}'),
            COALESCE((SELECT MAX({pk}) FROM {table}), 0),
            TRUE
        );
        """
    )


def upgrade() -> None:
    # Transactions are inserted during account refresh; ensure sequence is aligned
    _reset_sequence("transactions", "id")

    # PlaidTransactionMeta also uses an integer PK; align to be safe
    _reset_sequence("plaid_transaction_meta", "id")


def downgrade() -> None:
    # No-op: sequence positions are safe to leave as-is.
    pass

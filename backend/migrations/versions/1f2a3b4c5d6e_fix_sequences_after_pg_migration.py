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
    """Align the underlying sequence/identity for ``table.pk`` with the max(pk).

    Handles both legacy SERIAL-backed columns and modern IDENTITY columns.
    If no owned sequence exists (e.g., not an autoincrement integer), this is a no-op.
    """
    op.execute(
        f"""
        DO $$
        DECLARE
            seq_name text;
            max_id bigint;
        BEGIN
            -- Locate any sequence owned by table.column via catalog joins (works for SERIAL and IDENTITY)
            SELECT format('%I.%I', nsp.nspname, seq.relname)
            INTO seq_name
            FROM pg_class AS seq
            JOIN pg_namespace AS nsp ON nsp.oid = seq.relnamespace
            JOIN pg_depend AS dep ON dep.objid = seq.oid AND dep.deptype IN ('a','i')
            JOIN pg_class AS tbl ON tbl.oid = dep.refobjid
            JOIN pg_attribute AS att ON att.attrelid = tbl.oid AND att.attnum = dep.refobjsubid
            WHERE seq.relkind = 'S'
              AND tbl.relname = '{table}'
              AND att.attname = '{pk}'
            LIMIT 1;

            IF seq_name IS NOT NULL THEN
                EXECUTE format('SELECT COALESCE(MAX(%I), 0) FROM %I', '{pk}', '{table}') INTO max_id;
                IF max_id < 1 THEN
                    -- Initialize empty/new sequences so nextval() returns 1
                    EXECUTE format('SELECT setval(%L, 1, FALSE)', seq_name);
                ELSE
                    EXECUTE format('SELECT setval(%L, %s, TRUE)', seq_name, max_id);
                END IF;
            END IF;
        END
        $$;
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

"""Last refresehd to datetime

Revision ID: 18b0e9bdfb29
Revises: 7665737c5164
Create Date: 2025-04-09 19:13:47.828780

"""
from alembic import op
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, DateTime


# revision identifiers, used by Alembic.
revision = '18b0e9bdfb29'
down_revision = '7665737c5164'
branch_labels = None
depends_on = None


# Define temporary table for direct manipulation
accounts = table('accounts',
    column('id', sa.Integer),
    column('last_refreshed', sa.String)
)


def upgrade():
    connection = op.get_bind()

    # 1. Add the new column
    op.add_column('accounts', sa.Column('last_refreshed_new', sa.DateTime(), nullable=True))

    # 2. Migrate and convert data
    results = connection.execute(sa.text("SELECT id, last_refreshed FROM accounts"))
    for row in results:
        try:
            dt = datetime.fromisoformat(row['last_refreshed'])
            connection.execute(
                sa.text("UPDATE accounts SET last_refreshed_new = :dt WHERE id = :id"),
                {"dt": dt, "id": row["id"]}
            )
        except Exception:
            pass  # skip or log

    # 3. Drop the old column
    with op.batch_alter_table('accounts') as batch_op:
        batch_op.drop_column('last_refreshed')

    # 4. Rename the new column
    with op.batch_alter_table('accounts') as batch_op:
        batch_op.alter_column('last_refreshed_new', new_column_name='last_refreshed')


def downgrade():
    with op.batch_alter_table('accounts') as batch_op:
        batch_op.add_column(sa.Column('last_refreshed_str', sa.String(length=64), nullable=True))
    
    connection = op.get_bind()
    results = connection.execute(sa.text("SELECT id, last_refreshed FROM accounts"))
    for row in results:
        try:
            dt_str = row["last_refreshed"].isoformat()
            connection.execute(
                sa.text("UPDATE accounts SET last_refreshed_str = :dt WHERE id = :id"),
                {"dt": dt_str, "id": row["id"]}
            )
        except Exception:
            pass

    with op.batch_alter_table('accounts') as batch_op:
        batch_op.drop_column('last_refreshed')
        batch_op.alter_column('last_refreshed_str', new_column_name='last_refreshed')

    # ### end Alembic commands ###

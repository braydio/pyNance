"""last_synced to last_refreshed

Revision ID: 72127368ea72
Revises: d3d3082d65f5
Create Date: 2025-04-27 19:26:16.443262

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '72127368ea72'
down_revision = 'd3d3082d65f5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('plaid_accounts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_refreshed', sa.DateTime(), nullable=True))
        batch_op.drop_column('last_synced')

    with op.batch_alter_table('teller_accounts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_refreshed', sa.DateTime(), nullable=True))
        batch_op.drop_column('last_synced')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('teller_accounts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_synced', sa.DATETIME(), nullable=True))
        batch_op.drop_column('last_refreshed')

    with op.batch_alter_table('plaid_accounts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_synced', sa.DATETIME(), nullable=True))
        batch_op.drop_column('last_refreshed')

    # ### end Alembic commands ###

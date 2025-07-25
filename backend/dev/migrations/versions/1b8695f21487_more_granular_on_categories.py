"""More granular on categories

Revision ID: 1b8695f21487
Revises: 1a013aa715bd
Create Date: 2025-05-04 18:45:27.325506

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1b8695f21487'
down_revision = '1a013aa715bd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('categories', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_category_composite', ['primary_category', 'detailed_category'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('categories', schema=None) as batch_op:
        batch_op.drop_constraint('uq_category_composite', type_='unique')

    # ### end Alembic commands ###

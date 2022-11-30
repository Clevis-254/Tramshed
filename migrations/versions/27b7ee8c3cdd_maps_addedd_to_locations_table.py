"""maps addedd to locations table

Revision ID: 27b7ee8c3cdd
Revises: a26cbc448347
Create Date: 2022-11-25 16:37:48.505334

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '27b7ee8c3cdd'
down_revision = 'a26cbc448347'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('location', schema=None) as batch_op:
        batch_op.add_column(sa.Column('maps', sa.String(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('location', schema=None) as batch_op:
        batch_op.drop_column('maps')

    # ### end Alembic commands ###

"""empty message

Revision ID: 42e67e158013
Revises: aee96be0dced
Create Date: 2022-11-30 14:15:13.970638

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '42e67e158013'
down_revision = 'aee96be0dced'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('save_user_datas', sa.Column('date', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('save_user_datas', 'date')
    # ### end Alembic commands ###

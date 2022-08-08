"""empty message

Revision ID: ec5c078b1296
Revises: e32d8440113d
Create Date: 2022-07-22 10:24:50.101219

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ec5c078b1296'
down_revision = 'e32d8440113d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('patrons',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.Text(), nullable=True),
    sa.Column('status', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('wait_reactions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=True),
    sa.Column('uid', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('messages',
    sa.Column('link', sa.Text(), autoincrement=False, nullable=False),
    sa.Column('start_msg', sa.Boolean(), nullable=True),
    sa.Column('timeout', sa.Float(), nullable=True),
    sa.Column('speed_type', sa.Integer(), nullable=True),
    sa.Column('content_type', sa.Text(), nullable=True),
    sa.Column('message', sa.Text(), nullable=True),
    sa.Column('next_msg', sa.Text(), nullable=True),
    sa.Column('wait_reaction_id', sa.Integer(), nullable=True),
    sa.Column('referal_block', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['next_msg'], ['messages.link'], ),
    sa.ForeignKeyConstraint(['wait_reaction_id'], ['wait_reactions.id'], ),
    sa.PrimaryKeyConstraint('link'),
    sa.UniqueConstraint('link')
    )
    op.create_table('reactions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('text', sa.Text(), nullable=True),
    sa.Column('wait_reaction_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['wait_reaction_id'], ['wait_reactions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('buttons',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('parrent_message_link', sa.Text(), nullable=False),
    sa.Column('number', sa.Integer(), nullable=True),
    sa.Column('next_message_link', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['next_message_link'], ['messages.link'], ),
    sa.ForeignKeyConstraint(['parrent_message_link'], ['messages.link'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('media',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('file_data', sa.LargeBinary(), nullable=False),
    sa.Column('tg_id', sa.Text(), nullable=True),
    sa.Column('parrent_message_link', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['parrent_message_link'], ['messages.link'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('media')
    op.drop_table('buttons')
    op.drop_table('reactions')
    op.drop_table('messages')
    op.drop_table('wait_reactions')
    op.drop_table('patrons')
    # ### end Alembic commands ###

"""add UserWallet model to track available funds

Revision ID: 29f802a05436
Revises: ec1f5dccea8a
Create Date: 2024-06-19 20:33:25.445066

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '29f802a05436'
down_revision: Union[str, None] = 'ec1f5dccea8a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('expense_user_wallet',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('digital_balance', sa.Float(), nullable=True),
    sa.Column('cash_balance', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['expense_users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('expense_user_wallet')
    # ### end Alembic commands ###
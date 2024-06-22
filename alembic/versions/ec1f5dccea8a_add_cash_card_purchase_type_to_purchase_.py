"""add cash/card purchase type to purchase model

Revision ID: ec1f5dccea8a
Revises: 3315a039650f
Create Date: 2024-06-16 14:22:21.214033

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ec1f5dccea8a'
down_revision: Union[str, None] = '3315a039650f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('expense_purchases', sa.Column('type', sa.Enum('CASH', 'CARD', name='purchasetype'), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('expense_purchases', 'type')
    # ### end Alembic commands ###
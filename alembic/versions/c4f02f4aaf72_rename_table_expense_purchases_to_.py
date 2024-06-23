"""Rename table expense_purchases to expense_transactions

Revision ID: c4f02f4aaf72
Revises: 29f802a05436
Create Date: 2024-06-23 13:27:25.731525

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4f02f4aaf72'
down_revision: Union[str, None] = '29f802a05436'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.rename_table('expense_purchases', 'expense_transactions')


def downgrade():
    op.rename_table('expense_transactions', 'expense_purchases')

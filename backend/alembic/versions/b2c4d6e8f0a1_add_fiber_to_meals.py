"""add fiber to meals

Revision ID: b2c4d6e8f0a1
Revises: a9ba83f151cd
Create Date: 2026-07-10 16:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c4d6e8f0a1'
down_revision: Union[str, Sequence[str], None] = 'a9ba83f151cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('meals', sa.Column('fiber', sa.Float(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('meals', 'fiber')

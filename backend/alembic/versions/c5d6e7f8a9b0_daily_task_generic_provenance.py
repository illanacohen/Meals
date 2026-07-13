"""add daily_task source_module entity priority status

Revision ID: c5d6e7f8a9b0
Revises: b4c5d6e7f8a9
Create Date: 2026-07-12 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c5d6e7f8a9b0'
down_revision: Union[str, Sequence[str], None] = 'b4c5d6e7f8a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('daily_tasks') as batch:
        batch.add_column(sa.Column('source_module', sa.String(), nullable=True))
        batch.add_column(sa.Column('source_entity', sa.String(), nullable=True))
        batch.add_column(sa.Column('priority', sa.Integer(), nullable=False, server_default='3'))
        batch.add_column(sa.Column('status', sa.String(), nullable=False, server_default='pending'))


def downgrade() -> None:
    with op.batch_alter_table('daily_tasks') as batch:
        batch.drop_column('status')
        batch.drop_column('priority')
        batch.drop_column('source_entity')
        batch.drop_column('source_module')

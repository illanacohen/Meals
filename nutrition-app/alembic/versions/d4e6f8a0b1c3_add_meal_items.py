"""add meal items

Revision ID: d4e6f8a0b1c3
Revises: c3d5e7f9a0b2
Create Date: 2026-07-10 17:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4e6f8a0b1c3'
down_revision: Union[str, Sequence[str], None] = 'c3d5e7f9a0b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'meal_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('meal_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('grams', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['meal_id'], ['meals.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_meal_items_id'), 'meal_items', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_meal_items_id'), table_name='meal_items')
    op.drop_table('meal_items')

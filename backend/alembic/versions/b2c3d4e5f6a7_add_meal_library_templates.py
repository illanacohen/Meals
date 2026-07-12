"""add meal library templates

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-10 18:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'meal_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('calories', sa.Float(), nullable=False),
        sa.Column('protein', sa.Float(), nullable=False),
        sa.Column('carbs', sa.Float(), nullable=False),
        sa.Column('fat', sa.Float(), nullable=False),
        sa.Column('fiber', sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_meal_templates_id'), 'meal_templates', ['id'], unique=False)
    op.create_index(op.f('ix_meal_templates_name'), 'meal_templates', ['name'], unique=True)

    op.create_table(
        'meal_template_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(), nullable=False),
        sa.Column('grams', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['template_id'], ['meal_templates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_meal_template_items_id'), 'meal_template_items', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_meal_template_items_id'), table_name='meal_template_items')
    op.drop_table('meal_template_items')
    op.drop_index(op.f('ix_meal_templates_name'), table_name='meal_templates')
    op.drop_index(op.f('ix_meal_templates_id'), table_name='meal_templates')
    op.drop_table('meal_templates')

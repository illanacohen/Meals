"""add meal plans, slots and daily goals

Revision ID: c3d5e7f9a0b2
Revises: b2c4d6e8f0a1
Create Date: 2026-07-10 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d5e7f9a0b2'
down_revision: Union[str, Sequence[str], None] = 'b2c4d6e8f0a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'daily_goals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('calories', sa.Float(), nullable=False),
        sa.Column('protein', sa.Float(), nullable=False),
        sa.Column('fat', sa.Float(), nullable=False),
        sa.Column('carbs', sa.Float(), nullable=False),
        sa.Column('fiber', sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_daily_goals_id'), 'daily_goals', ['id'], unique=False)
    op.create_index(op.f('ix_daily_goals_date'), 'daily_goals', ['date'], unique=True)

    op.create_table(
        'meal_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_meal_plans_id'), 'meal_plans', ['id'], unique=False)
    op.create_index(op.f('ix_meal_plans_date'), 'meal_plans', ['date'], unique=True)

    op.create_table(
        'meal_slots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('label', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['plan_id'], ['meal_plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plan_id', 'position', name='uq_meal_slots_plan_position'),
    )
    op.create_index(op.f('ix_meal_slots_id'), 'meal_slots', ['id'], unique=False)

    with op.batch_alter_table('meals') as batch_op:
        batch_op.add_column(sa.Column('slot_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_meals_slot_id_meal_slots',
            'meal_slots',
            ['slot_id'],
            ['id'],
            ondelete='SET NULL',
        )


def downgrade() -> None:
    with op.batch_alter_table('meals') as batch_op:
        batch_op.drop_constraint('fk_meals_slot_id_meal_slots', type_='foreignkey')
        batch_op.drop_column('slot_id')

    op.drop_index(op.f('ix_meal_slots_id'), table_name='meal_slots')
    op.drop_table('meal_slots')
    op.drop_index(op.f('ix_meal_plans_date'), table_name='meal_plans')
    op.drop_index(op.f('ix_meal_plans_id'), table_name='meal_plans')
    op.drop_table('meal_plans')
    op.drop_index(op.f('ix_daily_goals_date'), table_name='daily_goals')
    op.drop_index(op.f('ix_daily_goals_id'), table_name='daily_goals')
    op.drop_table('daily_goals')

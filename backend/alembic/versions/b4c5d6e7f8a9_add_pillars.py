"""add pillars and link habits meals workouts tasks

Revision ID: b4c5d6e7f8a9
Revises: a3b4c5d6e7f8
Create Date: 2026-07-12 22:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b4c5d6e7f8a9'
down_revision: Union[str, Sequence[str], None] = 'a3b4c5d6e7f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'pillars',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(), nullable=True),
        sa.Column('color', sa.String(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plan_id', 'name', name='uq_pillars_plan_name'),
    )
    op.create_index(op.f('ix_pillars_id'), 'pillars', ['id'], unique=False)
    op.create_index(op.f('ix_pillars_plan_id'), 'pillars', ['plan_id'], unique=False)

    with op.batch_alter_table('habits') as batch:
        batch.add_column(sa.Column('pillar_id', sa.Integer(), nullable=True))
        batch.create_index(op.f('ix_habits_pillar_id'), ['pillar_id'], unique=False)
        batch.create_foreign_key(
            'fk_habits_pillar_id',
            'pillars',
            ['pillar_id'],
            ['id'],
            ondelete='SET NULL',
        )

    with op.batch_alter_table('plan_tasks') as batch:
        batch.add_column(sa.Column('pillar_id', sa.Integer(), nullable=True))
        batch.create_index(op.f('ix_plan_tasks_pillar_id'), ['pillar_id'], unique=False)
        batch.create_foreign_key(
            'fk_plan_tasks_pillar_id',
            'pillars',
            ['pillar_id'],
            ['id'],
            ondelete='SET NULL',
        )

    with op.batch_alter_table('daily_tasks') as batch:
        batch.add_column(sa.Column('pillar_id', sa.Integer(), nullable=True))
        batch.create_index(op.f('ix_daily_tasks_pillar_id'), ['pillar_id'], unique=False)
        batch.create_foreign_key(
            'fk_daily_tasks_pillar_id',
            'pillars',
            ['pillar_id'],
            ['id'],
            ondelete='SET NULL',
        )

    with op.batch_alter_table('workout_programs') as batch:
        batch.add_column(sa.Column('pillar_id', sa.Integer(), nullable=True))
        batch.create_index(op.f('ix_workout_programs_pillar_id'), ['pillar_id'], unique=False)
        batch.create_foreign_key(
            'fk_workout_programs_pillar_id',
            'pillars',
            ['pillar_id'],
            ['id'],
            ondelete='SET NULL',
        )

    with op.batch_alter_table('meal_plans') as batch:
        batch.add_column(sa.Column('pillar_id', sa.Integer(), nullable=True))
        batch.create_index(op.f('ix_meal_plans_pillar_id'), ['pillar_id'], unique=False)
        batch.create_foreign_key(
            'fk_meal_plans_pillar_id',
            'pillars',
            ['pillar_id'],
            ['id'],
            ondelete='SET NULL',
        )


def downgrade() -> None:
    with op.batch_alter_table('meal_plans') as batch:
        batch.drop_constraint('fk_meal_plans_pillar_id', type_='foreignkey')
        batch.drop_index(op.f('ix_meal_plans_pillar_id'))
        batch.drop_column('pillar_id')

    with op.batch_alter_table('workout_programs') as batch:
        batch.drop_constraint('fk_workout_programs_pillar_id', type_='foreignkey')
        batch.drop_index(op.f('ix_workout_programs_pillar_id'))
        batch.drop_column('pillar_id')

    with op.batch_alter_table('daily_tasks') as batch:
        batch.drop_constraint('fk_daily_tasks_pillar_id', type_='foreignkey')
        batch.drop_index(op.f('ix_daily_tasks_pillar_id'))
        batch.drop_column('pillar_id')

    with op.batch_alter_table('plan_tasks') as batch:
        batch.drop_constraint('fk_plan_tasks_pillar_id', type_='foreignkey')
        batch.drop_index(op.f('ix_plan_tasks_pillar_id'))
        batch.drop_column('pillar_id')

    with op.batch_alter_table('habits') as batch:
        batch.drop_constraint('fk_habits_pillar_id', type_='foreignkey')
        batch.drop_index(op.f('ix_habits_pillar_id'))
        batch.drop_column('pillar_id')

    op.drop_index(op.f('ix_pillars_plan_id'), table_name='pillars')
    op.drop_index(op.f('ix_pillars_id'), table_name='pillars')
    op.drop_table('pillars')

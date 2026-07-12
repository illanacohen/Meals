"""add goal plans and related modules

Revision ID: f1a2b3c4d5e6
Revises: e8f9a0b1c2d3
Create Date: 2026-07-12 11:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'e8f9a0b1c2d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('goal_type', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('duration_weeks', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('strategy_notes', sa.Text(), nullable=True),
        sa.Column('user_profile_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['user_profile_id'], ['user_profiles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_plans_id'), 'plans', ['id'], unique=False)

    op.create_table(
        'habits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('frequency', sa.String(), nullable=False),
        sa.Column('target_value', sa.Float(), nullable=True),
        sa.Column('target_unit', sa.String(), nullable=True),
        sa.Column('time_of_day', sa.String(), nullable=True),
        sa.Column('difficulty', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_habits_id'), 'habits', ['id'], unique=False)
    op.create_index(op.f('ix_habits_plan_id'), 'habits', ['plan_id'], unique=False)

    op.create_table(
        'habit_completions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('habit_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('completed', sa.Boolean(), nullable=False),
        sa.Column('notes', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['habit_id'], ['habits.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('habit_id', 'date', name='uq_habit_completions_habit_date'),
    )
    op.create_index(op.f('ix_habit_completions_id'), 'habit_completions', ['id'], unique=False)
    op.create_index(op.f('ix_habit_completions_date'), 'habit_completions', ['date'], unique=False)

    op.create_table(
        'workout_programs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plan_id'),
    )
    op.create_index(op.f('ix_workout_programs_id'), 'workout_programs', ['id'], unique=False)

    op.create_table(
        'workout_days',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('program_id', sa.Integer(), nullable=False),
        sa.Column('week_number', sa.Integer(), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['program_id'], ['workout_programs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_workout_days_id'), 'workout_days', ['id'], unique=False)

    op.create_table(
        'workout_exercises',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('day_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('sets', sa.Integer(), nullable=True),
        sa.Column('reps', sa.String(), nullable=True),
        sa.Column('rest_seconds', sa.Integer(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('progression_notes', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['day_id'], ['workout_days.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_workout_exercises_id'), 'workout_exercises', ['id'], unique=False)

    op.create_table(
        'daily_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('task_type', sa.String(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('completed', sa.Boolean(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plan_id', 'date', 'title', 'task_type', name='uq_daily_tasks_plan_date_title_type'),
    )
    op.create_index(op.f('ix_daily_tasks_id'), 'daily_tasks', ['id'], unique=False)
    op.create_index(op.f('ix_daily_tasks_plan_id'), 'daily_tasks', ['plan_id'], unique=False)
    op.create_index(op.f('ix_daily_tasks_date'), 'daily_tasks', ['date'], unique=False)

    op.create_table(
        'progress_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('weight_kg', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('adherence_percent', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_progress_entries_id'), 'progress_entries', ['id'], unique=False)
    op.create_index(op.f('ix_progress_entries_plan_id'), 'progress_entries', ['plan_id'], unique=False)
    op.create_index(op.f('ix_progress_entries_date'), 'progress_entries', ['date'], unique=False)

    with op.batch_alter_table('meal_plans') as batch:
        batch.add_column(sa.Column('goal_plan_id', sa.Integer(), nullable=True))
        batch.create_index(op.f('ix_meal_plans_goal_plan_id'), ['goal_plan_id'], unique=False)
        batch.create_foreign_key(
            'fk_meal_plans_goal_plan_id_plans',
            'plans',
            ['goal_plan_id'],
            ['id'],
            ondelete='SET NULL',
        )


def downgrade() -> None:
    with op.batch_alter_table('meal_plans') as batch:
        batch.drop_constraint('fk_meal_plans_goal_plan_id_plans', type_='foreignkey')
        batch.drop_index(op.f('ix_meal_plans_goal_plan_id'))
        batch.drop_column('goal_plan_id')

    op.drop_index(op.f('ix_progress_entries_date'), table_name='progress_entries')
    op.drop_index(op.f('ix_progress_entries_plan_id'), table_name='progress_entries')
    op.drop_index(op.f('ix_progress_entries_id'), table_name='progress_entries')
    op.drop_table('progress_entries')

    op.drop_index(op.f('ix_daily_tasks_date'), table_name='daily_tasks')
    op.drop_index(op.f('ix_daily_tasks_plan_id'), table_name='daily_tasks')
    op.drop_index(op.f('ix_daily_tasks_id'), table_name='daily_tasks')
    op.drop_table('daily_tasks')

    op.drop_index(op.f('ix_workout_exercises_id'), table_name='workout_exercises')
    op.drop_table('workout_exercises')
    op.drop_index(op.f('ix_workout_days_id'), table_name='workout_days')
    op.drop_table('workout_days')
    op.drop_index(op.f('ix_workout_programs_id'), table_name='workout_programs')
    op.drop_table('workout_programs')

    op.drop_index(op.f('ix_habit_completions_date'), table_name='habit_completions')
    op.drop_index(op.f('ix_habit_completions_id'), table_name='habit_completions')
    op.drop_table('habit_completions')
    op.drop_index(op.f('ix_habits_plan_id'), table_name='habits')
    op.drop_index(op.f('ix_habits_id'), table_name='habits')
    op.drop_table('habits')

    op.drop_index(op.f('ix_plans_id'), table_name='plans')
    op.drop_table('plans')

"""Daily Planner tables: schedule policy, blocks, templates, plan tasks; extend daily_tasks.

Revision ID: a3b4c5d6e7f8
Revises: f1a2b3c4d5e6
Create Date: 2026-07-12 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a3b4c5d6e7f8'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'day_schedule_policies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_profile_id', sa.Integer(), nullable=True),
        sa.Column('wake_time', sa.Time(), nullable=False),
        sa.Column('sleep_time', sa.Time(), nullable=False),
        sa.Column('work_pattern', sa.String(), nullable=False),
        sa.Column('work_start', sa.Time(), nullable=True),
        sa.Column('work_end', sa.Time(), nullable=True),
        sa.Column('training_days', sa.JSON(), nullable=True),
        sa.Column('training_hour', sa.Time(), nullable=True),
        sa.Column('meals_per_day', sa.Integer(), nullable=False),
        sa.Column('block1_ratio', sa.Float(), nullable=False),
        sa.Column('block2_ratio', sa.Float(), nullable=False),
        sa.Column('block3_ratio', sa.Float(), nullable=False),
        sa.Column('delay_first_meal', sa.Boolean(), nullable=False),
        sa.Column('timezone', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['user_profile_id'], ['user_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_profile_id'),
    )
    op.create_index(op.f('ix_day_schedule_policies_id'), 'day_schedule_policies', ['id'], unique=False)

    op.create_table(
        'task_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('default_friction', sa.Integer(), nullable=False),
        sa.Column('default_priority', sa.Integer(), nullable=False),
        sa.Column('default_duration_minutes', sa.Integer(), nullable=False),
        sa.Column('default_block_preference', sa.String(), nullable=False),
        sa.Column('is_system', sa.Boolean(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_task_templates_id'), 'task_templates', ['id'], unique=False)
    op.create_index(op.f('ix_task_templates_code'), 'task_templates', ['code'], unique=True)

    op.create_table(
        'day_blocks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('block_type', sa.String(), nullable=False),
        sa.Column('starts_at', sa.DateTime(), nullable=False),
        sa.Column('ends_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plan_id', 'date', 'block_type', name='uq_day_blocks_plan_date_type'),
    )
    op.create_index(op.f('ix_day_blocks_id'), 'day_blocks', ['id'], unique=False)
    op.create_index(op.f('ix_day_blocks_plan_id'), 'day_blocks', ['plan_id'], unique=False)
    op.create_index(op.f('ix_day_blocks_date'), 'day_blocks', ['date'], unique=False)

    op.create_table(
        'plan_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('habit_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('friction', sa.Integer(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('frequency', sa.String(), nullable=False),
        sa.Column('preferred_block', sa.String(), nullable=False),
        sa.Column('forbidden_blocks', sa.JSON(), nullable=True),
        sa.Column('depends_on_plan_task_id', sa.Integer(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['depends_on_plan_task_id'], ['plan_tasks.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['habit_id'], ['habits.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['template_id'], ['task_templates.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_plan_tasks_id'), 'plan_tasks', ['id'], unique=False)
    op.create_index(op.f('ix_plan_tasks_plan_id'), 'plan_tasks', ['plan_id'], unique=False)

    with op.batch_alter_table('daily_tasks') as batch:
        batch.add_column(sa.Column('plan_task_id', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('block_type', sa.String(), nullable=True))
        batch.add_column(sa.Column('estimated_duration_minutes', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('scheduled_time', sa.DateTime(), nullable=True))
        batch.create_foreign_key(
            'fk_daily_tasks_plan_task_id',
            'plan_tasks',
            ['plan_task_id'],
            ['id'],
            ondelete='SET NULL',
        )


def downgrade() -> None:
    with op.batch_alter_table('daily_tasks') as batch:
        batch.drop_constraint('fk_daily_tasks_plan_task_id', type_='foreignkey')
        batch.drop_column('scheduled_time')
        batch.drop_column('estimated_duration_minutes')
        batch.drop_column('block_type')
        batch.drop_column('plan_task_id')

    op.drop_index(op.f('ix_plan_tasks_plan_id'), table_name='plan_tasks')
    op.drop_index(op.f('ix_plan_tasks_id'), table_name='plan_tasks')
    op.drop_table('plan_tasks')

    op.drop_index(op.f('ix_day_blocks_date'), table_name='day_blocks')
    op.drop_index(op.f('ix_day_blocks_plan_id'), table_name='day_blocks')
    op.drop_index(op.f('ix_day_blocks_id'), table_name='day_blocks')
    op.drop_table('day_blocks')

    op.drop_index(op.f('ix_task_templates_code'), table_name='task_templates')
    op.drop_index(op.f('ix_task_templates_id'), table_name='task_templates')
    op.drop_table('task_templates')

    op.drop_index(op.f('ix_day_schedule_policies_id'), table_name='day_schedule_policies')
    op.drop_table('day_schedule_policies')

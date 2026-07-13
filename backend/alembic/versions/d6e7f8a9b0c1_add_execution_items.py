"""add execution_items dynamic items completions proposals

Revision ID: d6e7f8a9b0c1
Revises: c5d6e7f8a9b0
Create Date: 2026-07-12 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd6e7f8a9b0c1'
down_revision: Union[str, Sequence[str], None] = 'c5d6e7f8a9b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'execution_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('pillar_id', sa.Integer(), nullable=True),
        sa.Column('source_module', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('recurrence_rule', sa.String(), nullable=False),
        sa.Column('schedule_rule', sa.JSON(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('estimated_duration', sa.Integer(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('habit_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['habit_id'], ['habits.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['pillar_id'], ['pillars.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_execution_items_id'), 'execution_items', ['id'], unique=False)
    op.create_index(op.f('ix_execution_items_plan_id'), 'execution_items', ['plan_id'], unique=False)
    op.create_index(op.f('ix_execution_items_pillar_id'), 'execution_items', ['pillar_id'], unique=False)
    op.create_index(op.f('ix_execution_items_habit_id'), 'execution_items', ['habit_id'], unique=False)

    op.create_table(
        'execution_completions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('execution_item_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('completed', sa.Boolean(), nullable=False),
        sa.Column('notes', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['execution_item_id'], ['execution_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('execution_item_id', 'date', name='uq_execution_completions_item_date'),
    )
    op.create_index(op.f('ix_execution_completions_id'), 'execution_completions', ['id'], unique=False)
    op.create_index(op.f('ix_execution_completions_execution_item_id'), 'execution_completions', ['execution_item_id'], unique=False)
    op.create_index(op.f('ix_execution_completions_date'), 'execution_completions', ['date'], unique=False)

    op.create_table(
        'dynamic_execution_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=True),
        sa.Column('pillar_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('completed', sa.Boolean(), nullable=False),
        sa.Column('created_by_user', sa.Boolean(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['pillar_id'], ['pillars.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_dynamic_execution_items_id'), 'dynamic_execution_items', ['id'], unique=False)
    op.create_index(op.f('ix_dynamic_execution_items_plan_id'), 'dynamic_execution_items', ['plan_id'], unique=False)
    op.create_index(op.f('ix_dynamic_execution_items_pillar_id'), 'dynamic_execution_items', ['pillar_id'], unique=False)
    op.create_index(op.f('ix_dynamic_execution_items_due_date'), 'dynamic_execution_items', ['due_date'], unique=False)

    op.create_table(
        'plan_proposals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_plan_proposals_id'), 'plan_proposals', ['id'], unique=False)
    op.create_index(op.f('ix_plan_proposals_plan_id'), 'plan_proposals', ['plan_id'], unique=False)

    with op.batch_alter_table('daily_tasks') as batch:
        batch.add_column(sa.Column('execution_item_id', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('dynamic_execution_item_id', sa.Integer(), nullable=True))
        batch.create_index(op.f('ix_daily_tasks_execution_item_id'), ['execution_item_id'], unique=False)
        batch.create_index(op.f('ix_daily_tasks_dynamic_execution_item_id'), ['dynamic_execution_item_id'], unique=False)
        batch.create_foreign_key(
            'fk_daily_tasks_execution_item_id',
            'execution_items',
            ['execution_item_id'],
            ['id'],
            ondelete='SET NULL',
        )
        batch.create_foreign_key(
            'fk_daily_tasks_dynamic_execution_item_id',
            'dynamic_execution_items',
            ['dynamic_execution_item_id'],
            ['id'],
            ondelete='SET NULL',
        )

    # Backfill ExecutionItems from legacy PlanTasks (Plan remains source of truth going forward)
    conn = op.get_bind()
    plan_tasks = conn.execute(
        sa.text(
            'SELECT id, plan_id, template_id, habit_id, pillar_id, title, friction, '
            'priority, duration_minutes, frequency, preferred_block, active '
            'FROM plan_tasks'
        )
    ).fetchall()
    for pt in plan_tasks:
        (
            pt_id,
            plan_id,
            template_id,
            habit_id,
            pillar_id,
            title,
            friction,
            priority,
            duration_minutes,
            frequency,
            preferred_block,
            active,
        ) = pt
        template_code = None
        category = None
        if template_id is not None:
            row = conn.execute(
                sa.text('SELECT code, category FROM task_templates WHERE id = :id'),
                {'id': template_id},
            ).fetchone()
            if row:
                template_code, category = row[0], row[1]
        source_module = 'habits' if habit_id else 'planner'
        recurrence = frequency if frequency in ('daily', 'weekdays') else 'daily'
        import json

        schedule = json.dumps(
            {'preferred_block': preferred_block or 'any', 'friction': friction or 3}
        )
        meta = json.dumps(
            {
                'template_code': template_code,
                'category': category,
                'legacy_plan_task_id': pt_id,
            }
        )
        conn.execute(
            sa.text(
                'INSERT INTO execution_items '
                '(plan_id, pillar_id, source_module, title, recurrence_rule, schedule_rule, '
                'priority, estimated_duration, active, metadata, habit_id) '
                'VALUES (:plan_id, :pillar_id, :source_module, :title, :recurrence_rule, '
                ':schedule_rule, :priority, :estimated_duration, :active, :metadata, :habit_id)'
            ),
            {
                'plan_id': plan_id,
                'pillar_id': pillar_id,
                'source_module': source_module,
                'title': title,
                'recurrence_rule': recurrence,
                'schedule_rule': schedule,
                'priority': priority or 3,
                'estimated_duration': duration_minutes or 5,
                'active': bool(active),
                'metadata': meta,
                'habit_id': habit_id,
            },
        )


def downgrade() -> None:
    with op.batch_alter_table('daily_tasks') as batch:
        batch.drop_constraint('fk_daily_tasks_dynamic_execution_item_id', type_='foreignkey')
        batch.drop_constraint('fk_daily_tasks_execution_item_id', type_='foreignkey')
        batch.drop_index(op.f('ix_daily_tasks_dynamic_execution_item_id'))
        batch.drop_index(op.f('ix_daily_tasks_execution_item_id'))
        batch.drop_column('dynamic_execution_item_id')
        batch.drop_column('execution_item_id')

    op.drop_index(op.f('ix_plan_proposals_plan_id'), table_name='plan_proposals')
    op.drop_index(op.f('ix_plan_proposals_id'), table_name='plan_proposals')
    op.drop_table('plan_proposals')

    op.drop_index(op.f('ix_dynamic_execution_items_due_date'), table_name='dynamic_execution_items')
    op.drop_index(op.f('ix_dynamic_execution_items_pillar_id'), table_name='dynamic_execution_items')
    op.drop_index(op.f('ix_dynamic_execution_items_plan_id'), table_name='dynamic_execution_items')
    op.drop_index(op.f('ix_dynamic_execution_items_id'), table_name='dynamic_execution_items')
    op.drop_table('dynamic_execution_items')

    op.drop_index(op.f('ix_execution_completions_date'), table_name='execution_completions')
    op.drop_index(op.f('ix_execution_completions_execution_item_id'), table_name='execution_completions')
    op.drop_index(op.f('ix_execution_completions_id'), table_name='execution_completions')
    op.drop_table('execution_completions')

    op.drop_index(op.f('ix_execution_items_habit_id'), table_name='execution_items')
    op.drop_index(op.f('ix_execution_items_pillar_id'), table_name='execution_items')
    op.drop_index(op.f('ix_execution_items_plan_id'), table_name='execution_items')
    op.drop_index(op.f('ix_execution_items_id'), table_name='execution_items')
    op.drop_table('execution_items')

"""remove habit coach tables and execution_mode

Revision ID: e8f9a0b1c2d3
Revises: d7e8f9a0b1c2
Create Date: 2026-07-11 16:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e8f9a0b1c2d3'
down_revision: Union[str, Sequence[str], None] = 'd7e8f9a0b1c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f('ix_habit_day_logs_date'), table_name='habit_day_logs')
    op.drop_index(op.f('ix_habit_day_logs_id'), table_name='habit_day_logs')
    op.drop_table('habit_day_logs')
    op.drop_column('user_profiles', 'execution_mode')


def downgrade() -> None:
    op.add_column(
        'user_profiles',
        sa.Column('execution_mode', sa.String(), nullable=False, server_default='structured'),
    )
    op.create_table(
        'habit_day_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('principle_id', sa.String(), nullable=False),
        sa.Column('message', sa.String(), nullable=False),
        sa.Column('science', sa.String(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('execution_mode', sa.String(), nullable=False),
        sa.Column('action_completed', sa.Boolean(), nullable=False),
        sa.Column('negotiations', sa.Integer(), nullable=True),
        sa.Column('victories', sa.JSON(), nullable=True),
        sa.Column('snacks_avoided', sa.Integer(), nullable=False),
        sa.Column('plan_changes', sa.Integer(), nullable=False),
        sa.Column('meals_completed', sa.Integer(), nullable=False),
        sa.Column('notes', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date', name='uq_habit_day_logs_date'),
    )
    op.create_index(op.f('ix_habit_day_logs_id'), 'habit_day_logs', ['id'], unique=False)
    op.create_index(op.f('ix_habit_day_logs_date'), 'habit_day_logs', ['date'], unique=True)

"""add user_contexts aggregate

Revision ID: e7f8a9b0c1d2
Revises: d6e7f8a9b0c1
Create Date: 2026-07-12 23:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e7f8a9b0c1d2'
down_revision: Union[str, Sequence[str], None] = 'd6e7f8a9b0c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_contexts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_profile_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        # Identity
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('sex', sa.String(), nullable=True),
        sa.Column('height_cm', sa.Float(), nullable=True),
        sa.Column('weight_kg', sa.Float(), nullable=True),
        # Daily schedule
        sa.Column('wake_time', sa.Time(), nullable=True),
        sa.Column('sleep_time', sa.Time(), nullable=True),
        sa.Column('working_hours', sa.JSON(), nullable=True),
        sa.Column('preferred_training_time', sa.Time(), nullable=True),
        sa.Column('preferred_meal_times', sa.JSON(), nullable=True),
        sa.Column('timezone', sa.String(), nullable=True),
        # Preferences
        sa.Column('preferences', sa.JSON(), nullable=True),
        sa.Column('favorite_foods', sa.JSON(), nullable=True),
        sa.Column('disliked_foods', sa.JSON(), nullable=True),
        sa.Column('preferred_training_style', sa.String(), nullable=True),
        sa.Column('preferred_learning_style', sa.String(), nullable=True),
        # Constraints
        sa.Column('dietary_restrictions', sa.JSON(), nullable=True),
        sa.Column('food_intolerances', sa.JSON(), nullable=True),
        sa.Column('equipment', sa.JSON(), nullable=True),
        sa.Column('injuries', sa.JSON(), nullable=True),
        sa.Column('mobility_limitations', sa.JSON(), nullable=True),
        sa.Column('budget', sa.String(), nullable=True),
        sa.Column('available_time', sa.Integer(), nullable=True),
        sa.Column('gym_access', sa.Boolean(), nullable=True),
        sa.Column('work_schedule_constraints', sa.JSON(), nullable=True),
        # Execution profile
        sa.Column('energy_profile', sa.JSON(), nullable=True),
        sa.Column('motivation_style', sa.String(), nullable=True),
        sa.Column('discipline_level', sa.String(), nullable=True),
        sa.Column('planning_style', sa.String(), nullable=True),
        sa.Column('notification_preferences', sa.JSON(), nullable=True),
        # Behavior
        sa.Column('current_streaks', sa.JSON(), nullable=True),
        sa.Column('completed_habits', sa.JSON(), nullable=True),
        sa.Column('adherence_score', sa.Float(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('(CURRENT_TIMESTAMP)'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('(CURRENT_TIMESTAMP)'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['user_profile_id'], ['user_profiles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_profile_id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index(op.f('ix_user_contexts_id'), 'user_contexts', ['id'], unique=False)
    op.create_index(op.f('ix_user_contexts_user_profile_id'), 'user_contexts', ['user_profile_id'], unique=False)
    op.create_index(op.f('ix_user_contexts_user_id'), 'user_contexts', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_contexts_user_id'), table_name='user_contexts')
    op.drop_index(op.f('ix_user_contexts_user_profile_id'), table_name='user_contexts')
    op.drop_index(op.f('ix_user_contexts_id'), table_name='user_contexts')
    op.drop_table('user_contexts')

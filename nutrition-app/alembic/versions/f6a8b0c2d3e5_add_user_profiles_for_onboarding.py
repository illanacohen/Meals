"""add user profiles for onboarding

Revision ID: f6a8b0c2d3e5
Revises: e5f7a9b1c2d4
Create Date: 2026-07-10 18:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f6a8b0c2d3e5'
down_revision: Union[str, Sequence[str], None] = 'e5f7a9b1c2d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('age', sa.Integer(), nullable=False),
        sa.Column('sex', sa.String(), nullable=False),
        sa.Column('weight_kg', sa.Float(), nullable=False),
        sa.Column('height_cm', sa.Float(), nullable=False),
        sa.Column('goal', sa.String(), nullable=False),
        sa.Column('deficit_intensity', sa.String(), nullable=True),
        sa.Column('surplus_intensity', sa.String(), nullable=True),
        sa.Column('activity_level', sa.String(), nullable=False),
        sa.Column('training_days_per_week', sa.Integer(), nullable=False),
        sa.Column('training_time', sa.String(), nullable=True),
        sa.Column('wake_time', sa.Time(), nullable=True),
        sa.Column('sleep_time', sa.Time(), nullable=True),
        sa.Column('meals_per_day', sa.Integer(), nullable=False),
        sa.Column('hunger_pattern', sa.String(), nullable=True),
        sa.Column('prefers_larger_post_workout', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_user_profiles_id'), 'user_profiles', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_profiles_id'), table_name='user_profiles')
    op.drop_table('user_profiles')

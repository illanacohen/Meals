"""extend user profile optional onboarding fields

Revision ID: a1b2c3d4e5f6
Revises: f6a8b0c2d3e5
Create Date: 2026-07-10 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f6a8b0c2d3e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('user_profiles') as batch_op:
        batch_op.add_column(sa.Column('body_fat_percent', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('daily_steps', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('training_type', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('training_level', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('training_hour', sa.Time(), nullable=True))
        batch_op.add_column(sa.Column('food_preferences', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('excluded_foods', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('budget_level', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('cooking_time_minutes', sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('user_profiles') as batch_op:
        batch_op.drop_column('cooking_time_minutes')
        batch_op.drop_column('budget_level')
        batch_op.drop_column('excluded_foods')
        batch_op.drop_column('food_preferences')
        batch_op.drop_column('training_hour')
        batch_op.drop_column('training_level')
        batch_op.drop_column('training_type')
        batch_op.drop_column('daily_steps')
        batch_op.drop_column('body_fat_percent')

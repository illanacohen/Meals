"""rename user_profiles.sex to gender

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-10 18:40:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('user_profiles') as batch_op:
        batch_op.alter_column('sex', new_column_name='gender')


def downgrade() -> None:
    with op.batch_alter_table('user_profiles') as batch_op:
        batch_op.alter_column('gender', new_column_name='sex')

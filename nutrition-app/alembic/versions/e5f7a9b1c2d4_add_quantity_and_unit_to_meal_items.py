"""add quantity and unit to meal items

Revision ID: e5f7a9b1c2d4
Revises: d4e6f8a0b1c3
Create Date: 2026-07-10 18:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e5f7a9b1c2d4'
down_revision: Union[str, Sequence[str], None] = 'd4e6f8a0b1c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('meal_items') as batch_op:
        batch_op.add_column(sa.Column('quantity', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('unit', sa.String(), nullable=True))

    op.execute("UPDATE meal_items SET quantity = grams, unit = 'g' WHERE quantity IS NULL")

    with op.batch_alter_table('meal_items') as batch_op:
        batch_op.alter_column('quantity', existing_type=sa.Float(), nullable=False)
        batch_op.alter_column(
            'unit',
            existing_type=sa.String(),
            nullable=False,
            server_default='g',
        )


def downgrade() -> None:
    with op.batch_alter_table('meal_items') as batch_op:
        batch_op.drop_column('unit')
        batch_op.drop_column('quantity')

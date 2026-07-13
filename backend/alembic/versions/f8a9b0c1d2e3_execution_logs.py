"""add execution_logs; migrate from execution_completions

Revision ID: f8a9b0c1d2e3
Revises: e7f8a9b0c1d2
Create Date: 2026-07-13 00:10:00.000000

"""
import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f8a9b0c1d2e3'
down_revision: Union[str, Sequence[str], None] = 'e7f8a9b0c1d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'execution_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('execution_item_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('logged_at_time', sa.Time(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['execution_item_id'], ['execution_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('execution_item_id', 'date', name='uq_execution_logs_item_date'),
    )
    op.create_index(op.f('ix_execution_logs_id'), 'execution_logs', ['id'], unique=False)
    op.create_index(
        op.f('ix_execution_logs_execution_item_id'),
        'execution_logs',
        ['execution_item_id'],
        unique=False,
    )
    op.create_index(op.f('ix_execution_logs_date'), 'execution_logs', ['date'], unique=False)

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'execution_completions' in inspector.get_table_names():
        rows = conn.execute(
            sa.text(
                'SELECT execution_item_id, date, completed, notes FROM execution_completions'
            )
        ).fetchall()
        for row in rows:
            status = 'executed_smoothly' if row[2] else 'skipped'
            meta_json = json.dumps({'notes': row[3]}) if row[3] else None
            conn.execute(
                sa.text(
                    'INSERT INTO execution_logs '
                    '(execution_item_id, date, status, logged_at_time, metadata) '
                    'VALUES (:item_id, :date, :status, NULL, :metadata)'
                ),
                {
                    'item_id': row[0],
                    'date': row[1],
                    'status': status,
                    'metadata': meta_json,
                },
            )
        op.drop_index(op.f('ix_execution_completions_date'), table_name='execution_completions')
        op.drop_index(
            op.f('ix_execution_completions_execution_item_id'),
            table_name='execution_completions',
        )
        op.drop_index(op.f('ix_execution_completions_id'), table_name='execution_completions')
        op.drop_table('execution_completions')


def downgrade() -> None:
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
    op.create_index(
        op.f('ix_execution_completions_execution_item_id'),
        'execution_completions',
        ['execution_item_id'],
        unique=False,
    )
    op.create_index(op.f('ix_execution_completions_date'), 'execution_completions', ['date'], unique=False)

    conn = op.get_bind()
    rows = conn.execute(
        sa.text('SELECT execution_item_id, date, status FROM execution_logs')
    ).fetchall()
    for row in rows:
        conn.execute(
            sa.text(
                'INSERT INTO execution_completions '
                '(execution_item_id, date, completed, notes) '
                'VALUES (:item_id, :date, :completed, NULL)'
            ),
            {
                'item_id': row[0],
                'date': row[1],
                'completed': 0 if row[2] == 'skipped' else 1,
            },
        )

    op.drop_index(op.f('ix_execution_logs_date'), table_name='execution_logs')
    op.drop_index(op.f('ix_execution_logs_execution_item_id'), table_name='execution_logs')
    op.drop_index(op.f('ix_execution_logs_id'), table_name='execution_logs')
    op.drop_table('execution_logs')

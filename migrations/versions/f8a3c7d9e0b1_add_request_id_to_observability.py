"""add request_id to inference_traces and inference_spans

Adds request_id column to both tables for grouping traces
that belong to the same user query across multiple graph invocations.

Revision ID: f8a3c7d9e0b1
Revises: ce59b2fb541f
Create Date: 2026-05-26 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f8a3c7d9e0b1'
down_revision: Union[str, None] = 'ce59b2fb541f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('inference_traces', sa.Column('request_id', sa.String(), nullable=True))
    op.add_column('inference_spans', sa.Column('request_id', sa.String(), nullable=True))
    op.create_index(op.f('ix_inference_traces_request_id'), 'inference_traces', ['request_id'], unique=False)
    op.create_index(op.f('ix_inference_spans_request_id'), 'inference_spans', ['request_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_inference_spans_request_id'), table_name='inference_spans')
    op.drop_index(op.f('ix_inference_traces_request_id'), table_name='inference_traces')
    op.drop_column('inference_spans', 'request_id')
    op.drop_column('inference_traces', 'request_id')

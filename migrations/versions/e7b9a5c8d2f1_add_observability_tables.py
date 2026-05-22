"""Add observability tables

Revision ID: e7b9a5c8d2f1
Revises: d1acaed3df10
Create Date: 2026-05-06 16:38:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e7b9a5c8d2f1'
down_revision: Union[str, None] = 'd1acaed3df10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Create inference_traces table
    op.create_table(
        'inference_traces',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trace_id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('input_preview', sa.Text(), nullable=True),
        sa.Column('output_preview', sa.Text(), nullable=True),
        sa.Column('total_latency', sa.Float(), nullable=True),
        sa.Column('total_tokens', sa.Integer(), nullable=True),
        sa.Column('total_cost', sa.Float(), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('scores', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inference_traces_name'), 'inference_traces', ['name'], unique=False)
    op.create_index(op.f('ix_inference_traces_session_id'), 'inference_traces', ['session_id'], unique=False)
    op.create_index(op.f('ix_inference_traces_status'), 'inference_traces', ['status'], unique=False)
    op.create_index(op.f('ix_inference_traces_timestamp'), 'inference_traces', ['timestamp'], unique=False)
    op.create_index(op.f('ix_inference_traces_trace_id'), 'inference_traces', ['trace_id'], unique=True)

    # 2. Create inference_spans table
    op.create_table(
        'inference_spans',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trace_id', sa.String(), nullable=False),
        sa.Column('span_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('span_type', sa.String(), nullable=True),
        sa.Column('model', sa.String(), nullable=True),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('total_tokens', sa.Integer(), nullable=True),
        sa.Column('input_cost', sa.Float(), nullable=True),
        sa.Column('output_cost', sa.Float(), nullable=True),
        sa.Column('total_cost', sa.Float(), nullable=True),
        sa.Column('latency', sa.Float(), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('input_data', sa.Text(), nullable=True),
        sa.Column('output_data', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['trace_id'], ['inference_traces.trace_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inference_spans_model'), 'inference_spans', ['model'], unique=False)
    op.create_index(op.f('ix_inference_spans_name'), 'inference_spans', ['name'], unique=False)
    op.create_index(op.f('ix_inference_spans_span_id'), 'inference_spans', ['span_id'], unique=True)
    op.create_index(op.f('ix_inference_spans_span_type'), 'inference_spans', ['span_type'], unique=False)
    op.create_index(op.f('ix_inference_spans_start_time'), 'inference_spans', ['start_time'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_inference_spans_start_time'), table_name='inference_spans')
    op.drop_index(op.f('ix_inference_spans_span_type'), table_name='inference_spans')
    op.drop_index(op.f('ix_inference_spans_span_id'), table_name='inference_spans')
    op.drop_index(op.f('ix_inference_spans_name'), table_name='inference_spans')
    op.drop_index(op.f('ix_inference_spans_model'), table_name='inference_spans')
    op.drop_table('inference_spans')
    op.drop_index(op.f('ix_inference_traces_trace_id'), table_name='inference_traces')
    op.drop_index(op.f('ix_inference_traces_timestamp'), table_name='inference_traces')
    op.drop_index(op.f('ix_inference_traces_status'), table_name='inference_traces')
    op.drop_index(op.f('ix_inference_traces_session_id'), table_name='inference_traces')
    op.drop_index(op.f('ix_inference_traces_name'), table_name='inference_traces')
    op.drop_table('inference_traces')

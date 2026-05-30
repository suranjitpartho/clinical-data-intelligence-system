"""add sql_query to inference_traces (placed after total_cost)

PostgreSQL ADD COLUMN always appends at the end, so we rebuild the table
to position sql_query logically after total_cost.

Revision ID: ce59b2fb541f
Revises: d40d328ddad8
Create Date: 2026-05-22 16:46:42.659402

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ce59b2fb541f'
down_revision: Union[str, None] = 'd40d328ddad8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop FK so we can rebuild the parent table
    op.execute(
        "ALTER TABLE inference_spans DROP CONSTRAINT IF EXISTS inference_spans_trace_id_fkey"
    )

    # 2. Rename old table
    op.rename_table('inference_traces', 'inference_traces_old')

    # 3. Create new table with sql_query after total_cost
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
        sa.Column('sql_query', sa.Text(), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('scores', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 4. Copy data from old table
    op.execute("""
        INSERT INTO inference_traces (
            id, trace_id, session_id, name, status, timestamp,
            input_preview, output_preview,
            total_latency, total_tokens, total_cost,
            metadata_json, scores, error_message, synced_at
        )
        SELECT
            id, trace_id, session_id, name, status, timestamp,
            input_preview, output_preview,
            total_latency, total_tokens, total_cost,
            metadata_json, scores, error_message, synced_at
        FROM inference_traces_old
    """)

    # 5. Drop old table
    op.drop_table('inference_traces_old')

    # 6. Recreate indexes
    op.create_index(op.f('ix_inference_traces_name'), 'inference_traces', ['name'], unique=False)
    op.create_index(op.f('ix_inference_traces_session_id'), 'inference_traces', ['session_id'], unique=False)
    op.create_index(op.f('ix_inference_traces_status'), 'inference_traces', ['status'], unique=False)
    op.create_index(op.f('ix_inference_traces_timestamp'), 'inference_traces', ['timestamp'], unique=False)
    op.create_index(op.f('ix_inference_traces_trace_id'), 'inference_traces', ['trace_id'], unique=True)

    # 7. Recreate FK constraint
    op.execute(
        "ALTER TABLE inference_spans ADD CONSTRAINT inference_spans_trace_id_fkey "
        "FOREIGN KEY (trace_id) REFERENCES inference_traces(trace_id) ON DELETE CASCADE"
    )


def downgrade() -> None:
    # 1. Drop FK
    op.execute(
        "ALTER TABLE inference_spans DROP CONSTRAINT IF EXISTS inference_spans_trace_id_fkey"
    )

    # 2. Rename current table
    op.rename_table('inference_traces', 'inference_traces_new')

    # 3. Create old table without sql_query
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

    # 4. Copy data (excluding sql_query)
    op.execute("""
        INSERT INTO inference_traces (
            id, trace_id, session_id, name, status, timestamp,
            input_preview, output_preview,
            total_latency, total_tokens, total_cost,
            metadata_json, scores, error_message, synced_at
        )
        SELECT
            id, trace_id, session_id, name, status, timestamp,
            input_preview, output_preview,
            total_latency, total_tokens, total_cost,
            metadata_json, scores, error_message, synced_at
        FROM inference_traces_new
    """)

    # 5. Drop new table
    op.drop_table('inference_traces_new')

    # 6. Recreate indexes
    op.create_index(op.f('ix_inference_traces_name'), 'inference_traces', ['name'], unique=False)
    op.create_index(op.f('ix_inference_traces_session_id'), 'inference_traces', ['session_id'], unique=False)
    op.create_index(op.f('ix_inference_traces_status'), 'inference_traces', ['status'], unique=False)
    op.create_index(op.f('ix_inference_traces_timestamp'), 'inference_traces', ['timestamp'], unique=False)
    op.create_index(op.f('ix_inference_traces_trace_id'), 'inference_traces', ['trace_id'], unique=True)

    # 7. Recreate FK constraint
    op.execute(
        "ALTER TABLE inference_spans ADD CONSTRAINT inference_spans_trace_id_fkey "
        "FOREIGN KEY (trace_id) REFERENCES inference_traces(trace_id) ON DELETE CASCADE"
    )

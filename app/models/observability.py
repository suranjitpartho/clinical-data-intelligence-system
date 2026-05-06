import uuid
from sqlalchemy import Column, String, DateTime, Float, Integer, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base
import datetime

class InferenceTrace(Base):
    __tablename__ = "inference_traces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trace_id = Column(String, unique=True, index=True, nullable=False)
    session_id = Column(String, index=True)
    name = Column(String, index=True) # Feature identifier
    status = Column(String, index=True) # SUCCESS/ERROR
    timestamp = Column(DateTime(timezone=True), index=True)
    
    # Input/Output Previews
    input_preview = Column(Text)
    output_preview = Column(Text)
    
    # Aggregated Metrics (Denormalized for performance)
    total_latency = Column(Float, default=0.0)
    total_tokens = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    
    # Metadata & Feedback
    metadata_json = Column(JSONB, default={})
    scores = Column(JSONB, default={})
    error_message = Column(Text)
    
    synced_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    # Relationships
    spans = relationship("InferenceSpan", back_populates="trace", cascade="all, delete-orphan")

class InferenceSpan(Base):
    __tablename__ = "inference_spans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trace_id = Column(String, ForeignKey("inference_traces.trace_id", ondelete="CASCADE"), nullable=False)
    span_id = Column(String, unique=True, index=True, nullable=False)
    
    name = Column(String, index=True) # Node Name (e.g. REWRITE)
    span_type = Column(String, index=True) # GENERATION, TOOL, etc.
    model = Column(String, index=True)
    
    # Detailed Tokens
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    # Detailed Costs
    input_cost = Column(Float, default=0.0)
    output_cost = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)
    
    # Timing & Status
    latency = Column(Float, default=0.0)
    start_time = Column(DateTime(timezone=True), index=True)
    status = Column(String)
    error_message = Column(Text)
    
    # Raw Data (For SQL queries, etc.)
    input_data = Column(Text)
    output_data = Column(Text)

    # Relationships
    trace = relationship("InferenceTrace", back_populates="spans")

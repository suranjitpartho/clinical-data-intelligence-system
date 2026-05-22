import uuid
import datetime
from sqlalchemy import Column, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from app.db.base import Base

class SemanticQueryCache(Base):
    __tablename__ = "semantic_query_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_text = Column(Text, nullable=False, unique=True, index=True)
    vector = Column(Vector(1024), nullable=False)  # BGE-M3 model yields 1024-dimensional embeddings
    cached_sql = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

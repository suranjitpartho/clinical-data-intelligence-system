import uuid
from sqlalchemy import Column, String, DateTime, Text, func
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    user_query = Column(Text)
    tool_used = Column(String)  # SQL, RAG
    tool_query = Column(Text)   # The actual SQL or the Vector search query
    status = Column(String)     # Success, Failed, Fixed (if self-corrected)
    result_summary = Column(Text)

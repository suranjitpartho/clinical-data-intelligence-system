import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Float, func, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base

class Billing(Base):
    __tablename__ = "billing"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=False)
    
    amount = Column(Float, nullable=False)
    status = Column(String)  # Paid, Pending, Overdue
    payment_method = Column(String)
    invoice_date = Column(DateTime(timezone=True), server_default=func.now())
    
    appointment = relationship("Appointment", back_populates="billing")

class MedicalSupply(Base):
    __tablename__ = "medical_supplies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False)
    
    item_name = Column(String, nullable=False)
    quantity = Column(Integer, default=0)
    reorder_level = Column(Integer, default=10)
    supplier = Column(String)
    
    department = relationship("Department", back_populates="supplies")

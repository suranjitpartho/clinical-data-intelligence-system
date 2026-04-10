import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Text, Float, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.db.base import Base

class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("staff.id"), nullable=False)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False)
    
    appointment_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String)  # Scheduled, Completed, Cancelled
    reason = Column(Text)
    
    # Relationships
    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Staff", back_populates="appointments")
    note = relationship("ClinicalNote", back_populates="appointment", uselist=False)
    billing = relationship("Billing", back_populates="appointment", uselist=False)
    prescriptions = relationship("Prescription", back_populates="appointment")
    lab_results = relationship("LabResult", back_populates="appointment")

class ClinicalNote(Base):
    __tablename__ = "clinical_notes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=False)
    
    content = Column(Text, nullable=False)
    # Using 1024 dimensions for local powerful models like BGE-Large or BGE-M3
    vector = Column(Vector(1024))
    
    appointment = relationship("Appointment", back_populates="note")

class Prescription(Base):
    __tablename__ = "prescriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=False)
    
    medication = Column(String, nullable=False)
    dosage = Column(String, nullable=False)
    frequency = Column(String, nullable=False)
    duration = Column(String)
    notes = Column(Text)
    
    appointment = relationship("Appointment", back_populates="prescriptions")

class LabResult(Base):
    __tablename__ = "lab_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=False)
    
    test_name = Column(String, nullable=False)
    result_value = Column(Float)
    reference_range = Column(String)
    is_abnormal = Column(String) # For simple filtering
    
    appointment = relationship("Appointment", back_populates="lab_results")

import uuid
from sqlalchemy import Column, String, ForeignKey, Table, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base

class Department(Base):
    __tablename__ = "departments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    location = Column(String)  # e.g., "Level 2, North Wing"
    
    # Relationships
    staff = relationship("Staff", back_populates="department")
    supplies = relationship("MedicalSupply", back_populates="department")

class Staff(Base):
    __tablename__ = "staff"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # e.g., "Doctor", "Admin", "Nurse"
    specialisation = Column(String)
    email = Column(String, unique=True, index=True)
    
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    department = relationship("Department", back_populates="staff")
    
    appointments = relationship("Appointment", back_populates="doctor")

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nhi_number = Column(String, unique=True, index=True, nullable=False) # NZ Health Identifier
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(Date)
    gender = Column(String)
    email = Column(String, unique=True)
    phone = Column(String)
    address = Column(String)
    emergency_contact_name = Column(String)
    emergency_contact_phone = Column(String)
    
    appointments = relationship("Appointment", back_populates="patient")

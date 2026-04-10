from app.db.base import Base
from .core import Department, Staff, Patient
from .clinical import Appointment, ClinicalNote, Prescription, LabResult
from .business import Billing, MedicalSupply
from .logs import AuditLog

# This ensures all models are registered with the Base metadata
__all__ = [
    "Base",
    "Department",
    "Staff",
    "Patient",
    "Appointment",
    "ClinicalNote",
    "Prescription",
    "LabResult",
    "Billing",
    "MedicalSupply",
    "AuditLog"
]

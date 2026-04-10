import os
import uuid
import random
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.base import SessionLocal, engine
from app.models import (
    Department, Staff, Patient, Appointment, 
    ClinicalNote, Prescription, LabResult, 
    Billing, MedicalSupply, Base
)
from app.db.base import Base

fake = Faker(['en_NZ'])

# Medical Note Templates
NOTE_TEMPLATES = [
    "Patient presents with {symptom}. History of {condition}. Plan: {plan}.",
    "Follow-up for {condition}. Symptoms are {status}. Patient advised to {advice}.",
    "Routine checkup. Vital signs: {vitals}. Overall health is {status}. Follow-up in {time}.",
    "Emergency consultation. Patient reported {symptom} occurring for {duration}. Referred to {specialist}.",
]

SYMPTOMS = ["persistent cough", "lower back pain", "severe headache", "mild fever", "dizziness", "fatigue"]
CONDITIONS = ["hypertension", "type 2 diabetes", "seasonal allergies", "asthma", "moderate anxiety"]
PLANS = ["prescribed antibiotics", "ordered blood tests", "recommended rest", "increased dosage of current meds"]
STATUSES = ["improving", "stable", "worsening", "unsolved"]

def clear_db():
    print("Clearing existing data...")
    # Use raw SQL to truncate all tables and handle foreign key dependencies
    with engine.connect() as connection:
        connection.execute(text("TRUNCATE TABLE audit_logs, billing, prescriptions, lab_results, clinical_notes, appointments, medical_supplies, staff, patients, departments CASCADE;"))
        connection.commit()

def seed_departments(db: Session):
    print("Seeding departments...")
    depts = ["General Practice", "Cardiology", "Pediatrics", "Orthopedics", "Emergency"]
    locations = ["Floor 1, Wing A", "Floor 2, Wing B", "Floor 1, Wing C", "Floor 3, Wing A", "Ground Floor"]
    
    created_depts = []
    for i in range(len(depts)):
        d = Department(name=depts[i], location=locations[i])
        db.add(d)
        created_depts.append(d)
    db.commit()
    return created_depts

def seed_staff(db: Session, depts):
    print("Seeding staff...")
    roles = ["Doctor"] * 15 + ["Admin"] * 5
    created_staff = []
    for role in roles:
        dept = random.choice(depts)
        s = Staff(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            role=role,
            specialisation=fake.job() if role == "Doctor" else "Operations",
            email=fake.email(),
            department_id=dept.id
        )
        db.add(s)
        created_staff.append(s)
    db.commit()
    return created_staff

def seed_patients(db: Session, count=500):
    print(f"Seeding {count} patients...")
    created_patients = []
    for _ in range(count):
        # Generate fake NHI (3 letters 4 numbers)
        nhi = f"{fake.unique.bothify('???####').upper()}"
        p = Patient(
            nhi_number=nhi,
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            date_of_birth=fake.date_of_birth(minimum_age=1, maximum_age=95).isoformat(),
            gender=random.choice(["Male", "Female", "Other"]),
            email=fake.unique.email(),
            phone=fake.phone_number(),
            address=fake.address(),
            emergency_contact_name=fake.name(),
            emergency_contact_phone=fake.phone_number()
        )
        db.add(p)
        created_patients.append(p)
    db.commit()
    return created_patients

def seed_clinical_data(db: Session, patients, doctors, depts, count=5000):
    print(f"Seeding {count} appointments and related data...")
    doctors_only = [s for s in doctors if s.role == "Doctor"]
    
    for i in range(count):
        patient = random.choice(patients)
        doctor = random.choice(doctors_only)
        
        # Appointment date within last 2 years
        days_ago = random.randint(0, 730)
        appt_date = datetime.now() - timedelta(days=days_ago)
        
        appt = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            department_id=doctor.department_id,
            appointment_date=appt_date,
            status=random.choice(["Completed", "Completed", "Completed", "Cancelled"]),
            reason=fake.sentence()
        )
        db.add(appt)
        db.flush() # Get ID for relationships
        
        # Clinical Note
        note_text = random.choice(NOTE_TEMPLATES).format(
            symptom=random.choice(SYMPTOMS),
            condition=random.choice(CONDITIONS),
            plan=random.choice(PLANS),
            status=random.choice(STATUSES),
            advice=fake.sentence(),
            vitals=f"BP: {random.randint(110,140)}/{random.randint(70,90)}, HR: {random.randint(60,100)}",
            time=f"{random.randint(1,6)} months",
            duration=f"{random.randint(2,10)} days",
            specialist=random.choice(["Cardiology", "Neurology", "a specialist"])
        )
        note = ClinicalNote(appointment_id=appt.id, content=note_text)
        db.add(note)
        
        # Billing
        billing = Billing(
            appointment_id=appt.id,
            amount=random.uniform(50, 450),
            status=random.choice(["Paid", "Paid", "Pending"]),
            payment_method=random.choice(["Credit Card", "Eftpos", "Insurance"]),
            invoice_date=appt_date
        )
        db.add(billing)
        
        # Random Prescriptions (70% chance)
        if random.random() > 0.3:
            presc = Prescription(
                appointment_id=appt.id,
                medication=random.choice(["Amoxicillin", "Metformin", "Atorvastatin", "Lisinopril"]),
                dosage=f"{random.choice([5, 10, 20, 500])}mg",
                frequency="Once daily",
                duration=f"{random.randint(7, 30)} days"
            )
            db.add(presc)
            
        # Random Lab Results (50% chance)
        if random.random() > 0.5:
            lab = LabResult(
                appointment_id=appt.id,
                test_name=random.choice(["Full Blood Count", "Lipid Profile", "HbA1c", "Liver Function"]),
                result_value=f"{random.uniform(1.0, 10.0):.1f}",
                is_abnormal=random.choice(["No", "No", "Yes"])
            )
            db.add(lab)
        
        if i % 500 == 0:
            db.commit()
            print(f"Processed {i} clinical records...")
            
    db.commit()

def seed_supplies(db: Session, depts):
    print("Seeding medical supplies...")
    items = ["Sterile Gauze", "Syringes (5ml)", "Nitrile Gloves", "Adhesive Bandages", "Antiseptic Wipes"]
    for dept in depts:
        for item in items:
            s = MedicalSupply(
                item_name=item,
                quantity=random.randint(10, 200),
                reorder_level=20,
                supplier=fake.company(),
                department_id=dept.id
            )
            db.add(s)
    db.commit()

def run_seeding():
    db = SessionLocal()
    try:
        clear_db()
        depts = seed_departments(db)
        staff = seed_staff(db, depts)
        patients = seed_patients(db, count=500) # Full target: 500
        
        seed_clinical_data(db, patients, staff, depts, count=5000) # Full target: 5,000
        seed_supplies(db, depts)
        
        print("\n--- Seeding complete! ---")
        print("Note: Run the embedding script next to populate 'clinical_notes.vector'")
    finally:
        db.close()

if __name__ == "__main__":
    run_seeding()

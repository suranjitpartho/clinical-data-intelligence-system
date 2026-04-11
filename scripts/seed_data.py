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

# Master Clinical Map: Links everything logically across ALL 10 departments
CLINICAL_MAP = {
    "Cardiology": {
        "specialties": ["Cardiologist", "Cardiac Surgeon", "Cardiology Nurse"],
        "symptoms": ["chest pain", "palpitations", "shortness of breath", "fainting"],
        "conditions": ["Hypertension", "Atrial Fibrillation", "Tachycardia", "Heart Failure"],
        "labs": [
            {"test": "Lipid Profile", "range": "120-200 mg/dL", "min": 120, "max": 200, "unit": "mg/dL"},
            {"test": "Troponin", "range": "0-0.04 ng/mL", "min": 0, "max": 0.04, "unit": "ng/mL"}
        ],
        "meds": [
            {"name": "Atorvastatin", "dose": "20mg", "freq": "Once daily", "note": "Take at night"},
            {"name": "Lisinopril", "dose": "10mg", "freq": "Once daily", "note": "Monitor BP weekly"}
        ],
        "note_template": "Patient evaluated for {symptom}. ECG shows signs of {condition}. Commencing {med} {dose}. Follow-up in 2 weeks."
    },
    "Endocrinology": {
        "specialties": ["Endocrinologist", "Diabetologist"],
        "symptoms": ["increased thirst", "excessive fatigue", "unexplained weight loss"],
        "conditions": ["Type 2 Diabetes", "Hyperthyroidism", "Hypothyroidism", "Cushing Syndrome"],
        "labs": [
            {"test": "HbA1c", "range": "4.0-5.6%", "min": 4.0, "max": 5.6, "unit": "%"},
            {"test": "TSH", "range": "0.4-4.0 mIU/L", "min": 0.4, "max": 4.0, "unit": "mIU/L"}
        ],
        "meds": [
            {"name": "Metformin", "dose": "500mg", "freq": "Twice daily", "note": "Take with meals"},
            {"name": "Levothyroxine", "dose": "50mcg", "freq": "Once daily", "note": "Take 30 min before breakfast"}
        ],
        "note_template": "Initial screening for {condition}. Symptoms of {symptom} noted. Requested {lab}. Started {med} {dose}."
    },
    "General Practice": {
        "specialties": ["General Practitioner", "Family Nurse Practitioner"],
        "symptoms": ["mild fever", "persistent cough", "seasonal allergies", "sore throat"],
        "conditions": ["Influenza", "Vitamin D Deficiency", "GERD", "Mild Anxiety"],
        "labs": [
            {"test": "Full Blood Count", "range": "4.5-11.0 x10^9/L", "min": 4.5, "max": 11.0, "unit": "x10^9/L"},
            {"test": "Vitamin D", "range": "50-125 nmol/L", "min": 50, "max": 125, "unit": "nmol/L"}
        ],
        "meds": [
            {"name": "Amoxicillin", "dose": "500mg", "freq": "TID", "note": "Complete full course"},
            {"name": "Omeprazole", "dose": "20mg", "freq": "Once daily", "note": "Avoid spicy foods"}
        ],
        "note_template": "Routine consultation. Patient complains of {symptom}. Suspected {condition}. Prescription for {med} issued."
    },
    "Pediatrics": {
        "specialties": ["Pediatrician", "Pediatric Nurse"],
        "symptoms": ["rash", "ear pain", "persistent wheezing", "poor appetite"],
        "conditions": ["Ear Infection", "Childhood Asthma", "Eczema", "Tonsillitis"],
        "labs": [
            {"test": "Pediatric Iron", "range": "10-20 umol/L", "min": 10, "max": 20, "unit": "umol/L"}
        ],
        "meds": [
            {"name": "Salbutamol", "dose": "100mcg", "freq": "4 puffs daily", "note": "Use with spacer"},
            {"name": "Amoxicillin Suspension", "dose": "250mg/5mL", "freq": "Twice daily", "note": "Keep refrigerated"}
        ],
        "note_template": "Growth and development check. Current symptoms: {symptom}. Diagnosis: {condition}. Advised caretakers on {med} administration."
    },
    "Neurology": {
        "specialties": ["Neurologist", "Neurosurgeon", "Neurology Nurse"],
        "symptoms": ["severe dizziness", "blurred vision", "chronic migraines", "numerical confusion"],
        "conditions": ["Chronic Migraine", "Multiple Sclerosis", "Epilepsy", "Post-Concussion"],
        "labs": [
            {"test": "Vitamin B12", "range": "150-700 pmol/L", "min": 150, "max": 700, "unit": "pmol/L"}
        ],
        "meds": [
            {"name": "Sumatriptan", "dose": "50mg", "freq": "When needed", "note": "Take at onset of migraine"},
            {"name": "Gabapentin", "dose": "300mg", "freq": "TID", "note": "May cause drowsiness"}
        ],
        "note_template": "Neurological review. History of {condition}. Presenting with {symptom}. MRI Brain ordered. Commencing {med}."
    },
    "Orthopedics": {
        "specialties": ["Orthopedic Surgeon", "Physiotherapist"],
        "symptoms": ["joint stiffness", "lower back pain", "limited range of motion"],
        "conditions": ["Osteoarthritis", "Lumbar Herniation", "Ligament Tear"],
        "labs": [{"test": "Bone Density (T-Score)", "range": "1.0 to -1.0", "min": -1.0, "max": 1.0, "unit": "T-Score"}],
        "meds": [{"name": "Ibuprofen", "dose": "400mg", "freq": "TID PRN", "note": "Take with food"}],
        "note_template": "Musculoskeletal assessment for {symptom}. Suspected {condition}. Prescription for {med} given."
    },
    "Emergency": {
        "specialties": ["ER Physician", "Trauma Surgeon", "Triage Nurse"],
        "symptoms": ["acute trauma", "severe abdominal pain", "uncontrolled bleeding"],
        "conditions": ["Acute Appendicitis", "Concussion", "Fracture", "Internal Bleeding"],
        "labs": [{"test": "Lactate", "range": "0.5-2.2 mmol/L", "min": 0.5, "max": 2.2, "unit": "mmol/L"}],
        "meds": [{"name": "Morphine", "dose": "5mg", "freq": "STAT", "note": "Monitor respiratory rate"}],
        "note_template": "Emergent presentation with {symptom}. High probability of {condition}. Administered {med}. Urgent CT ordered."
    },
    "Radiology": {
        "specialties": ["Radiologist", "X-Ray Technician", "Sonographer"],
        "symptoms": ["localized pain", "structural abnormality"],
        "conditions": ["Fracture", "Soft Tissue Mass", "Pneumonia Signs"],
        "labs": [{"test": "Creatinine (Pre-Contrast)", "range": "60-110 umol/L", "min": 60, "max": 110, "unit": "umol/L"}],
        "meds": [{"name": "Iodinated Contrast", "dose": "100mL", "freq": "Once", "note": "Hydrate well post-procedure"}],
        "note_template": "Imaging study completed. Clinical indication: {symptom}. Findings suggestive of {condition}."
    },
    "Oncology": {
        "specialties": ["Oncologist", "Chemotherapy Nurse"],
        "symptoms": ["unexplained weight loss", "night sweats", "palpable mass"],
        "conditions": ["In-situ Carcinoma", "Lymphoma", "Metastatic Lesion"],
        "labs": [{"test": "Tumor Marker (CEA)", "range": "0-3.0 ng/mL", "min": 0, "max": 3.0, "unit": "ng/mL"}],
        "meds": [{"name": "Cyclophosphamide", "dose": "500mg", "freq": "Per cycle", "note": "Highly emetogenic"}],
        "note_template": "Follow-up for {condition}. Reports {symptom} since last cycle. CBC within limits. Continuing {med}."
    },
    "Dermatology": {
        "specialties": ["Dermatologist", "Dermpathologist"],
        "symptoms": ["atopic rash", "changing mole", "diffuse pruritus"],
        "conditions": ["Atopic Dermatitis", "Psoriasis", "Basal Cell Carcinoma"],
        "labs": [{"test": "Skin Punch Biopsy", "range": "Diagnostic", "min": 0, "max": 1, "unit": "N/A"}],
        "meds": [{"name": "Hydrocortisone Cream", "dose": "1%", "freq": "BID", "note": "Apply thinly to affected areas"}],
        "note_template": "Dermatological inspection. {symptom} observed. Diagnosis of {condition} confirmed. Patient to apply {med}."
    }
}

def clear_db():
    print("Clearing existing data...")
    with engine.connect() as connection:
        connection.execute(text("TRUNCATE TABLE audit_logs, billing, prescriptions, lab_results, clinical_notes, appointments, medical_supplies, staff, patients, departments CASCADE;"))
        connection.commit()

def seed_departments(db: Session):
    print("Seeding departments...")
    depts = [
        "General Practice", "Cardiology", "Pediatrics", "Orthopedics", "Emergency",
        "Neurology", "Radiology", "Oncology", "Endocrinology", "Dermatology"
    ]
    locations = [
        "Floor 1, Wing A", "Floor 2, Wing B", "Floor 1, Wing C", "Floor 3, Wing A", "Ground Floor",
        "Floor 4, Wing D", "Basement, Level 1", "Floor 2, Wing E", "Floor 3, Wing B", "Floor 1, Wing D"
    ]
    
    created_depts = []
    for i in range(len(depts)):
        d = Department(
            name=depts[i], 
            location=locations[i],
            operating_budget=random.uniform(500000, 2000000) # Realistic budget
        )
        db.add(d)
        created_depts.append(d)
    db.commit()
    return created_depts

def seed_staff(db: Session, depts):
    print("Seeding staff...")
    created_staff = []
    
    # 2 Doctors and 1 Nurse per department for logic consistency
    for dept in depts:
        # Get specialty from map if exists
        medical_info = CLINICAL_MAP.get(dept.name)
        specialties = medical_info["specialties"] if medical_info else ["General Practitioner"]
        
        for _ in range(3):
            is_doctor = random.random() > 0.3
            role = "Doctor" if is_doctor else "Nurse"
            
            s = Staff(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                role=role,
                specialisation=random.choice(specialties) if is_doctor else f"{dept.name} Nurse",
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
        nhi = f"{fake.unique.bothify('???####').upper()}"
        p = Patient(
            nhi_number=nhi,
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            date_of_birth=fake.date_of_birth(minimum_age=1, maximum_age=95),
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
    
    # Track risk per patient during this session
    patient_risks = {p.id: 0.0 for p in patients}
    
    for i in range(count):
        patient = random.choice(patients)
        doctor = random.choice(doctors_only)
        dept_name = db.query(Department).get(doctor.department_id).name
        
        # Determine age for risk factor
        age = (datetime.now().date() - patient.date_of_birth).days // 365
        if age > 65:
            patient_risks[patient.id] += 0.5 # Small increment per visit for elderly
        
        # Get logical mapping for this department
        med_logic = CLINICAL_MAP.get(dept_name, CLINICAL_MAP["General Practice"])
        
        # Department severity risk
        if dept_name in ["Oncology", "Emergency"]:
            patient_risks[patient.id] += 5.0
        elif dept_name == "Cardiology":
            patient_risks[patient.id] += 2.0
            
        # Appointment date
        days_ago = random.randint(0, 730)
        appt_date = datetime.now() - timedelta(days=days_ago)
        
        appt = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            department_id=doctor.department_id,
            appointment_date=appt_date,
            status=random.choice(["Completed", "Completed", "Completed", "Cancelled"]),
            reason=f"Consultation for {random.choice(med_logic['symptoms'])}"
        )
        db.add(appt)
        db.flush() 
        
        # Clinical Note (Semantic RAG Fuel)
        selected_symptom = random.choice(med_logic['symptoms'])
        selected_condition = random.choice(med_logic['conditions'])
        selected_med = random.choice(med_logic['meds'])
        selected_lab = random.choice(med_logic['labs'])
        
        note_text = med_logic['note_template'].format(
            symptom=selected_symptom,
            condition=selected_condition,
            med=selected_med['name'],
            dose=selected_med['dose'],
            lab=selected_lab['test']
        )
        note = ClinicalNote(appointment_id=appt.id, content=note_text)
        db.add(note)
        
        # Billing (Refined ranges)
        billing = Billing(
            appointment_id=appt.id,
            amount=random.uniform(80, 600),
            status=random.choice(["Paid", "Paid", "Pending"]),
            payment_method=random.choice(["Credit Card", "Eftpos", "Insurance"]),
            invoice_date=appt_date
        )
        db.add(billing)
        
        # Prescriptions
        if random.random() > 0.3:
            presc = Prescription(
                appointment_id=appt.id,
                medication=selected_med['name'],
                dosage=selected_med['dose'],
                frequency=selected_med['freq'],
                duration=f"{random.randint(7, 30)} days",
                notes=selected_med['note']
            )
            db.add(presc)
            
        # Lab Results (Calculated Abnormality)
        if random.random() > 0.4:
            lab_def = selected_lab
            if random.random() > 0.8: # 20% abnormal
                is_too_high = random.random() > 0.5
                val = lab_def['max'] + random.uniform(1.0, 10.0) if is_too_high else lab_def['min'] - random.uniform(1.0, 5.0)
                patient_risks[patient.id] += 15.0 # Significant risk jump for abnormal labs
            else:
                val = random.uniform(lab_def['min'], lab_def['max'])
            
            is_abnormal = "Yes" if (val < lab_def['min'] or val > lab_def['max']) else "No"
            
            lab = LabResult(
                appointment_id=appt.id,
                test_name=lab_def['test'],
                result_value=round(val, 2),
                reference_range=lab_def['range'],
                is_abnormal=is_abnormal
            )
            db.add(lab)
        
        if i % 1000 == 0:
            db.commit()
            print(f"Processed {i} clinical records...")

    # Final pass to save risk scores, capped at 100
    print("Updating patient risk profiles...")
    for p_id, risk in patient_risks.items():
        db.query(Patient).filter(Patient.id == p_id).update({"risk_profile": min(risk, 100.0)})
    
    db.commit()

def seed_supplies(db: Session, depts):
    print("Seeding medical supplies...")
    # Map supplies to departments
    SUPPLY_MAP = {
        "Cardiology": ["ECG Electrodes", "Cardiac Stents", "Heart Valves"],
        "Radiology": ["Contrast Agent", "Lead Aprons", "X-Ray Film"],
        "Pharmacy": ["Insulin Pens", "Saline Bags"],
        "Emergency": ["Trauma Gauze", "IV Kits", "Defibrillator Pads"]
    }
    
    items = ["Sterile Gauze", "Syringes (5ml)", "Nitrile Gloves"]
    for dept in depts:
        dept_items = items + SUPPLY_MAP.get(dept.name, [])
        for item in dept_items:
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
        patients = seed_patients(db, count=500)
        seed_clinical_data(db, patients, staff, depts, count=5000)
        seed_supplies(db, depts)
        print("\n--- Clinical Simulation Seeding complete! ---")
    finally:
        db.close()

if __name__ == "__main__":
    run_seeding()

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
    Billing, MedicalSupply, Diagnosis, ClinicalGuideline, Base
)

fake = Faker(['en_NZ'])

# Master Clinical Map — condition-driven architecture.
# Each condition owns its specific symptoms, medications, and lab tests.
# This ensures: reason → note → diagnosis → prescription → lab result are all medically coherent.
CLINICAL_MAP = {
    "Cardiology": {
        "doctor_specialties": ["Cardiologist", "Cardiac Surgeon"],
        "nurse_specialties": ["Cardiology Nurse"],
        "conditions": [
            {
                "name": "Hypertension", "icd": "I10",
                "symptoms": ["persistent headache", "dizziness", "shortness of breath on exertion"],
                "meds": [{"name": "Lisinopril", "dose": "10mg", "freq": "Once daily", "note": "Monitor BP weekly"}],
                "labs": [{"test": "Lipid Profile", "range": "120-200 mg/dL", "min": 120, "max": 200, "unit": "mg/dL"}]
            },
            {
                "name": "Atrial Fibrillation", "icd": "I48",
                "symptoms": ["palpitations", "fainting episodes", "irregular heartbeat"],
                "meds": [{"name": "Warfarin", "dose": "5mg", "freq": "Once daily", "note": "Monitor INR weekly"}],
                "labs": [{"test": "Troponin", "range": "0-0.04 ng/mL", "min": 0, "max": 0.04, "unit": "ng/mL"}]
            },
            {
                "name": "Tachycardia", "icd": "I47.1",
                "symptoms": ["rapid heartbeat", "chest pain", "palpitations"],
                "meds": [{"name": "Metoprolol", "dose": "25mg", "freq": "Twice daily", "note": "Do not stop abruptly"}],
                "labs": [{"test": "Troponin", "range": "0-0.04 ng/mL", "min": 0, "max": 0.04, "unit": "ng/mL"}]
            },
            {
                "name": "Heart Failure", "icd": "I50.9",
                "symptoms": ["shortness of breath", "ankle swelling", "persistent fatigue"],
                "meds": [{"name": "Furosemide", "dose": "40mg", "freq": "Once daily", "note": "Monitor potassium levels"}],
                "labs": [{"test": "Lipid Profile", "range": "120-200 mg/dL", "min": 120, "max": 200, "unit": "mg/dL"}]
            }
        ],
        "note_template": "Chief Complaint: Patient presented with {symptom}. On examination, BP was elevated and irregular rhythm noted. ECG conducted — findings consistent with {condition}. Patient counselled on lifestyle modifications including low-sodium diet and smoking cessation. Commencing {med} {dose}. Follow-up in 2 weeks or earlier if symptoms worsen."
    },
    "Endocrinology": {
        "doctor_specialties": ["Endocrinologist", "Diabetologist"],
        "nurse_specialties": ["Endocrinology Nurse"],
        "conditions": [
            {
                "name": "Type 2 Diabetes", "icd": "E11.9",
                "symptoms": ["increased thirst", "frequent urination", "excessive fatigue"],
                "meds": [{"name": "Metformin", "dose": "500mg", "freq": "Twice daily", "note": "Take with meals"}],
                "labs": [{"test": "HbA1c", "range": "4.0-5.6%", "min": 4.0, "max": 5.6, "unit": "%"}]
            },
            {
                "name": "Hypothyroidism", "icd": "E03.9",
                "symptoms": ["excessive fatigue", "unexplained weight gain", "cold intolerance"],
                "meds": [{"name": "Levothyroxine", "dose": "50mcg", "freq": "Once daily", "note": "Take 30 min before breakfast"}],
                "labs": [{"test": "TSH", "range": "0.4-4.0 mIU/L", "min": 0.4, "max": 4.0, "unit": "mIU/L"}]
            },
            {
                "name": "Hyperthyroidism", "icd": "E05.9",
                "symptoms": ["unexplained weight loss", "heat intolerance", "anxiety and tremors"],
                "meds": [{"name": "Carbimazole", "dose": "10mg", "freq": "Three times daily", "note": "Monitor blood count monthly"}],
                "labs": [{"test": "TSH", "range": "0.4-4.0 mIU/L", "min": 0.4, "max": 4.0, "unit": "mIU/L"}]
            },
            {
                "name": "Cushing Syndrome", "icd": "E24.9",
                "symptoms": ["unexplained weight gain", "facial rounding", "easy bruising"],
                "meds": [{"name": "Metyrapone", "dose": "250mg", "freq": "Four times daily", "note": "Take with food to reduce nausea"}],
                "labs": [{"test": "HbA1c", "range": "4.0-5.6%", "min": 4.0, "max": 5.6, "unit": "%"}]
            }
        ],
        "note_template": "Presenting complaint: {symptom} ongoing for several weeks. Clinical suspicion of {condition}. Laboratory investigations requested — {lab} results pending. BMI noted and dietary habits discussed. Starting {med} {dose} with instructions to take consistently. Patient advised to monitor symptoms and return in 4 weeks for results review."
    },
    "General Practice": {
        "doctor_specialties": ["General Practitioner", "Family Medicine Physician"],
        "nurse_specialties": ["Practice Nurse"],
        "conditions": [
            {
                "name": "Influenza", "icd": "J11.1",
                "symptoms": ["mild fever", "persistent cough", "sore throat"],
                "meds": [{"name": "Amoxicillin", "dose": "500mg", "freq": "TID", "note": "Complete full course"}],
                "labs": [{"test": "Full Blood Count", "range": "4.5-11.0 x10^9/L", "min": 4.5, "max": 11.0, "unit": "x10^9/L"}]
            },
            {
                "name": "Vitamin D Deficiency", "icd": "E55.9",
                "symptoms": ["bone pain", "muscle weakness", "seasonal fatigue"],
                "meds": [{"name": "Colecalciferol", "dose": "1000 IU", "freq": "Once daily", "note": "Take with a fatty meal"}],
                "labs": [{"test": "Vitamin D", "range": "50-125 nmol/L", "min": 50, "max": 125, "unit": "nmol/L"}]
            },
            {
                "name": "GERD", "icd": "K21.9",
                "symptoms": ["heartburn", "acid reflux after meals", "chest discomfort after eating"],
                "meds": [{"name": "Omeprazole", "dose": "20mg", "freq": "Once daily", "note": "Avoid spicy foods"}],
                "labs": [{"test": "Full Blood Count", "range": "4.5-11.0 x10^9/L", "min": 4.5, "max": 11.0, "unit": "x10^9/L"}]
            },
            {
                "name": "Mild Anxiety", "icd": "F41.1",
                "symptoms": ["persistent worry", "restlessness", "sleep disturbance"],
                "meds": [{"name": "Sertraline", "dose": "50mg", "freq": "Once daily", "note": "Allow 4-6 weeks for full effect"}],
                "labs": [{"test": "Full Blood Count", "range": "4.5-11.0 x10^9/L", "min": 4.5, "max": 11.0, "unit": "x10^9/L"}]
            }
        ],
        "note_template": "Routine consultation. Patient reports {symptom} persisting for approximately one week. No red flag symptoms identified. Observations within normal limits. Clinical impression: {condition}. Patient educated on self-care and hydration. Prescription for {med} issued. Advised to return if no improvement within 5 days."
    },
    "Pediatrics": {
        "doctor_specialties": ["Pediatrician", "Neonatologist"],
        "nurse_specialties": ["Pediatric Nurse"],
        "conditions": [
            {
                "name": "Ear Infection", "icd": "H66.9",
                "symptoms": ["ear pain", "irritability", "poor appetite"],
                "meds": [{"name": "Amoxicillin Suspension", "dose": "250mg/5mL", "freq": "Twice daily", "note": "Keep refrigerated"}],
                "labs": [{"test": "Pediatric Iron", "range": "10-20 umol/L", "min": 10, "max": 20, "unit": "umol/L"}]
            },
            {
                "name": "Childhood Asthma", "icd": "J45.9",
                "symptoms": ["persistent wheezing", "night cough", "shortness of breath on activity"],
                "meds": [{"name": "Salbutamol", "dose": "100mcg", "freq": "4 puffs daily", "note": "Use with spacer"}],
                "labs": [{"test": "Pediatric Iron", "range": "10-20 umol/L", "min": 10, "max": 20, "unit": "umol/L"}]
            },
            {
                "name": "Eczema", "icd": "L20.9",
                "symptoms": ["intense skin itching", "dry and flaky skin patches", "skin rash"],
                "meds": [{"name": "Hydrocortisone Cream", "dose": "1%", "freq": "BID", "note": "Apply thinly to affected areas only"}],
                "labs": [{"test": "Pediatric Iron", "range": "10-20 umol/L", "min": 10, "max": 20, "unit": "umol/L"}]
            },
            {
                "name": "Tonsillitis", "icd": "J03.9",
                "symptoms": ["sore throat", "difficulty swallowing", "poor appetite"],
                "meds": [{"name": "Amoxicillin Suspension", "dose": "250mg/5mL", "freq": "Twice daily", "note": "Keep refrigerated"}],
                "labs": [{"test": "Pediatric Iron", "range": "10-20 umol/L", "min": 10, "max": 20, "unit": "umol/L"}]
            }
        ],
        "note_template": "Paediatric consultation. Caretaker reports child presenting with {symptom}. Weight and height plotted on growth chart — within expected percentile. Clinical findings consistent with {condition}. Caretaker counselled on administration of {med} and importance of completing the full course. Follow-up in 1 week or sooner if fever develops."
    },
    "Neurology": {
        "doctor_specialties": ["Neurologist", "Neurosurgeon"],
        "nurse_specialties": ["Neurology Nurse"],
        "conditions": [
            {
                "name": "Chronic Migraine", "icd": "G43.0",
                "symptoms": ["severe throbbing headache", "light and sound sensitivity", "nausea with headache"],
                "meds": [{"name": "Sumatriptan", "dose": "50mg", "freq": "When needed", "note": "Take at onset of migraine"}],
                "labs": [{"test": "Vitamin B12", "range": "150-700 pmol/L", "min": 150, "max": 700, "unit": "pmol/L"}]
            },
            {
                "name": "Multiple Sclerosis", "icd": "G35",
                "symptoms": ["numbness and tingling in limbs", "muscle weakness", "blurred vision"],
                "meds": [{"name": "Gabapentin", "dose": "300mg", "freq": "TID", "note": "May cause drowsiness"}],
                "labs": [{"test": "Vitamin B12", "range": "150-700 pmol/L", "min": 150, "max": 700, "unit": "pmol/L"}]
            },
            {
                "name": "Epilepsy", "icd": "G40.9",
                "symptoms": ["seizure episodes", "brief confusion", "sudden loss of consciousness"],
                "meds": [{"name": "Levetiracetam", "dose": "500mg", "freq": "Twice daily", "note": "Do not miss doses"}],
                "labs": [{"test": "Vitamin B12", "range": "150-700 pmol/L", "min": 150, "max": 700, "unit": "pmol/L"}]
            },
            {
                "name": "Post-Concussion", "icd": "F07.81",
                "symptoms": ["persistent dizziness", "cognitive fog and difficulty concentrating", "chronic headache"],
                "meds": [{"name": "Amitriptyline", "dose": "10mg", "freq": "Once nightly", "note": "May cause morning drowsiness"}],
                "labs": [{"test": "Vitamin B12", "range": "150-700 pmol/L", "min": 150, "max": 700, "unit": "pmol/L"}]
            }
        ],
        "note_template": "Neurological review for known history of {condition}. Currently presenting with {symptom}. Cranial nerve examination unremarkable. Coordination and gait assessed — mild deficit noted. MRI Brain ordered urgently. Commenced {med} with instructions on dosage schedule. Patient warned regarding drowsiness and advised not to drive."
    },
    "Orthopedics": {
        "doctor_specialties": ["Orthopedic Surgeon", "Sports Medicine Physician"],
        "nurse_specialties": ["Orthopedic Nurse"],
        "conditions": [
            {
                "name": "Osteoarthritis", "icd": "M19.9",
                "symptoms": ["joint stiffness", "deep aching joint pain", "crepitus on movement"],
                "meds": [{"name": "Ibuprofen", "dose": "400mg", "freq": "TID PRN", "note": "Take with food"}],
                "labs": [{"test": "Bone Density (T-Score)", "range": "1.0 to -1.0", "min": -1.0, "max": 1.0, "unit": "T-Score"}]
            },
            {
                "name": "Lumbar Herniation", "icd": "M51.2",
                "symptoms": ["lower back pain", "leg numbness and tingling", "limited range of motion"],
                "meds": [{"name": "Diclofenac", "dose": "75mg", "freq": "Twice daily", "note": "Take with food, avoid with renal disease"}],
                "labs": [{"test": "Bone Density (T-Score)", "range": "1.0 to -1.0", "min": -1.0, "max": 1.0, "unit": "T-Score"}]
            },
            {
                "name": "Ligament Tear", "icd": "S83.2",
                "symptoms": ["acute joint instability", "sudden sharp pain on movement", "localised joint swelling"],
                "meds": [{"name": "Ibuprofen", "dose": "400mg", "freq": "TID PRN", "note": "Take with food"}],
                "labs": [{"test": "Bone Density (T-Score)", "range": "1.0 to -1.0", "min": -1.0, "max": 1.0, "unit": "T-Score"}]
            }
        ],
        "note_template": "Musculoskeletal assessment. Patient presents with {symptom} affecting daily function. Range of motion assessed — restricted lateral movement noted. X-ray requested. Clinical diagnosis: {condition}. Referred to physiotherapy. Prescribed {med} for short-term pain relief. Patient advised to apply ice pack and avoid strenuous activity."
    },
    "Emergency": {
        "doctor_specialties": ["ER Physician", "Trauma Surgeon"],
        "nurse_specialties": ["Triage Nurse", "Emergency Nurse"],
        "conditions": [
            {
                "name": "Acute Appendicitis", "icd": "K35.80",
                "symptoms": ["severe right-sided abdominal pain", "nausea and vomiting", "rebound abdominal tenderness"],
                "meds": [{"name": "Morphine", "dose": "5mg", "freq": "STAT", "note": "Monitor respiratory rate"}],
                "labs": [{"test": "Lactate", "range": "0.5-2.2 mmol/L", "min": 0.5, "max": 2.2, "unit": "mmol/L"}]
            },
            {
                "name": "Concussion", "icd": "S06.0X0A",
                "symptoms": ["head trauma", "brief loss of consciousness", "confusion and disorientation"],
                "meds": [{"name": "Paracetamol", "dose": "1g", "freq": "QID PRN", "note": "Avoid NSAIDs post-concussion"}],
                "labs": [{"test": "Lactate", "range": "0.5-2.2 mmol/L", "min": 0.5, "max": 2.2, "unit": "mmol/L"}]
            },
            {
                "name": "Fracture", "icd": "T14.8",
                "symptoms": ["acute trauma", "severe localised bone pain", "inability to bear weight"],
                "meds": [{"name": "Morphine", "dose": "5mg", "freq": "STAT", "note": "Monitor respiratory rate"}],
                "labs": [{"test": "Lactate", "range": "0.5-2.2 mmol/L", "min": 0.5, "max": 2.2, "unit": "mmol/L"}]
            },
            {
                "name": "Internal Bleeding", "icd": "R58",
                "symptoms": ["uncontrolled internal haemorrhage", "severe abdominal pain", "haemodynamic instability"],
                "meds": [{"name": "Tranexamic Acid", "dose": "1g IV", "freq": "STAT", "note": "Administer within 3 hours of injury"}],
                "labs": [{"test": "Lactate", "range": "0.5-2.2 mmol/L", "min": 0.5, "max": 2.2, "unit": "mmol/L"}]
            }
        ],
        "note_template": "Emergency presentation. Patient brought in with {symptom}. GCS assessed — patient alert and oriented. Vital signs: HR elevated, BP fluctuating. High clinical suspicion of {condition}. IV access established. {med} administered STAT as per emergency protocol. Urgent CT scan ordered. Surgical team alerted for standby."
    },
    "Radiology": {
        "doctor_specialties": ["Radiologist", "Interventional Radiologist"],
        "nurse_specialties": ["Radiology Nurse"],
        "conditions": [
            {
                "name": "Fracture", "icd": "T14.8",
                "symptoms": ["localised bone pain", "structural deformity on palpation", "acute trauma history"],
                "meds": [{"name": "Iodinated Contrast", "dose": "100mL", "freq": "Once", "note": "Hydrate well post-procedure"}],
                "labs": [{"test": "Creatinine (Pre-Contrast)", "range": "60-110 umol/L", "min": 60, "max": 110, "unit": "umol/L"}]
            },
            {
                "name": "Soft Tissue Mass", "icd": "R22.9",
                "symptoms": ["palpable soft tissue lump", "localised swelling", "structural abnormality on examination"],
                "meds": [{"name": "Iodinated Contrast", "dose": "100mL", "freq": "Once", "note": "Hydrate well post-procedure"}],
                "labs": [{"test": "Creatinine (Pre-Contrast)", "range": "60-110 umol/L", "min": 60, "max": 110, "unit": "umol/L"}]
            },
            {
                "name": "Pneumonia Signs", "icd": "J18.9",
                "symptoms": ["productive cough with consolidation signs", "chest tightness", "shortness of breath"],
                "meds": [{"name": "Iodinated Contrast", "dose": "100mL", "freq": "Once", "note": "Hydrate well post-procedure"}],
                "labs": [{"test": "Creatinine (Pre-Contrast)", "range": "60-110 umol/L", "min": 60, "max": 110, "unit": "umol/L"}]
            }
        ],
        "note_template": "Imaging referral. Clinical indication: {symptom} with suspected {condition}. Pre-procedure creatinine checked and hydration status confirmed. Imaging study completed without immediate complications. Radiological findings forwarded to referring team for clinical correlation. Patient advised to hydrate well and report any adverse contrast reactions."
    },
    "Oncology": {
        "doctor_specialties": ["Oncologist", "Haematologist"],
        "nurse_specialties": ["Chemotherapy Nurse", "Oncology Nurse"],
        "conditions": [
            {
                "name": "In-situ Carcinoma", "icd": "D09.9",
                "symptoms": ["unexplained weight loss", "persistent night sweats", "unexplained fatigue"],
                "meds": [{"name": "Cyclophosphamide", "dose": "500mg", "freq": "Per cycle", "note": "Highly emetogenic"}],
                "labs": [{"test": "Tumor Marker (CEA)", "range": "0-3.0 ng/mL", "min": 0, "max": 3.0, "unit": "ng/mL"}]
            },
            {
                "name": "Lymphoma", "icd": "C85.9",
                "symptoms": ["swollen lymph nodes", "drenching night sweats", "unexplained weight loss"],
                "meds": [{"name": "Rituximab", "dose": "375mg/m2", "freq": "Per cycle", "note": "Pre-medicate with antihistamine"}],
                "labs": [{"test": "Tumor Marker (CEA)", "range": "0-3.0 ng/mL", "min": 0, "max": 3.0, "unit": "ng/mL"}]
            },
            {
                "name": "Metastatic Lesion", "icd": "C80.0",
                "symptoms": ["palpable mass at distant site", "bone pain", "severe unexplained fatigue"],
                "meds": [{"name": "Cyclophosphamide", "dose": "500mg", "freq": "Per cycle", "note": "Highly emetogenic"}],
                "labs": [{"test": "Tumor Marker (CEA)", "range": "0-3.0 ng/mL", "min": 0, "max": 3.0, "unit": "ng/mL"}]
            }
        ],
        "note_template": "Oncology follow-up. Diagnosis: {condition}. Patient reports {symptom} since the last treatment cycle. Performance status assessed — ECOG Grade 1. CBC within acceptable limits for continued therapy. {med} cycle proceeding as planned. Anti-emetics and supportive care medications reviewed. Next follow-up scheduled in 3 weeks post-cycle."
    },
    "Dermatology": {
        "doctor_specialties": ["Dermatologist", "Dermatopathologist"],
        "nurse_specialties": ["Dermatology Nurse"],
        "conditions": [
            {
                "name": "Atopic Dermatitis", "icd": "L20.9",
                "symptoms": ["intense diffuse itching", "dry inflamed skin patches", "skin weeping and crusting"],
                "meds": [{"name": "Hydrocortisone Cream", "dose": "1%", "freq": "BID", "note": "Apply thinly to affected areas"}],
                "labs": [{"test": "Skin Punch Biopsy", "range": "Diagnostic", "min": 0, "max": 1, "unit": "N/A"}]
            },
            {
                "name": "Psoriasis", "icd": "L40.9",
                "symptoms": ["raised scaly silver plaques", "skin thickening", "joint pain associated with skin lesions"],
                "meds": [{"name": "Betamethasone Cream", "dose": "0.1%", "freq": "Once daily", "note": "Avoid prolonged use on face"}],
                "labs": [{"test": "Skin Punch Biopsy", "range": "Diagnostic", "min": 0, "max": 1, "unit": "N/A"}]
            },
            {
                "name": "Basal Cell Carcinoma", "icd": "C44.91",
                "symptoms": ["changing mole or skin lesion", "non-healing skin sore", "skin discolouration and ulceration"],
                "meds": [{"name": "Imiquimod Cream", "dose": "5%", "freq": "5 nights per week", "note": "Local skin reactions expected"}],
                "labs": [{"test": "Skin Punch Biopsy", "range": "Diagnostic", "min": 0, "max": 1, "unit": "N/A"}]
            }
        ],
        "note_template": "Dermatology consultation. Patient presents with {symptom}. Full skin examination performed — distribution and morphology of lesion documented. Dermoscopy performed. Clinical diagnosis: {condition}. Skin punch biopsy obtained and sent to pathology. {med} prescribed for symptomatic relief in the interim. Patient to avoid sun exposure and return for biopsy results in 10 days."
    }
}

def clear_db():
    print("Clearing existing data...")
    with engine.connect() as connection:
        connection.execute(text("TRUNCATE TABLE clinical_guidelines, diagnoses, audit_logs, billing, prescriptions, lab_results, clinical_notes, appointments, medical_supplies, staff, patients, departments CASCADE;"))
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
            operating_budget=random.uniform(500000, 2000000)
        )
        db.add(d)
        created_depts.append(d)
    db.commit()
    return created_depts

def seed_staff(db: Session, depts):
    print("Seeding staff...")
    created_staff = []
    
    # 2 Doctors and 1 Nurse per department — role is derived from specialty, not randomised
    for dept in depts:
        medical_info = CLINICAL_MAP.get(dept.name, {})
        doctor_specs = medical_info.get("doctor_specialties", ["General Practitioner"])
        nurse_specs = medical_info.get("nurse_specialties", [f"{dept.name} Nurse"])
        
        # Seed 2 doctors per department
        for _ in range(2):
            s = Staff(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                role="Doctor",
                specialisation=random.choice(doctor_specs),
                email=fake.email(),
                department_id=dept.id,
                salary=float(random.randint(220000, 380000))
            )
            db.add(s)
            created_staff.append(s)
        
        # Seed 1 nurse per department
        s = Staff(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            role="Nurse",
            specialisation=random.choice(nurse_specs),
            email=fake.email(),
            department_id=dept.id,
            salary=float(random.randint(80000, 120000))
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
            patient_risks[patient.id] += 0.5
        
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
        
        # --- Select condition FIRST — all other clinical variables derive from it ---
        # This ensures: reason -> note -> diagnosis -> prescription -> lab test are coherent
        condition_obj = random.choice(med_logic['conditions'])
        selected_condition = condition_obj['name']
        selected_icd = condition_obj['icd']
        selected_symptom = random.choice(condition_obj['symptoms'])
        selected_med = random.choice(condition_obj['meds'])
        selected_lab = random.choice(condition_obj['labs'])

        # Appointment status: Completed (75%) or Cancelled (25%)
        appt_status = random.choices(["Completed", "Cancelled"], weights=[75, 25], k=1)[0]
        # Reason = patient's self-reported complaint, same symptom as the note
        appt_reason = f"Patient reporting {selected_symptom}"

        appt = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            department_id=doctor.department_id,
            appointment_date=appt_date,
            status=appt_status,
            reason=appt_reason
        )
        db.add(appt)
        db.flush()

        # Only Completed appointments generate downstream clinical records
        if appt_status != "Completed":
            if i % 1000 == 0:
                db.commit()
                print(f"Processed {i} clinical records...")
            continue

        # 1. Store Structured Diagnosis
        diag = Diagnosis(
            appointment_id=appt.id,
            condition_name=selected_condition,
            icd_code=selected_icd,
            is_primary="Yes"
        )
        db.add(diag)

        # 2. Store Narrative Note — references the same symptom, condition, med as everything else
        note_text = med_logic['note_template'].format(
            symptom=selected_symptom,
            condition=selected_condition,
            med=selected_med['name'],
            dose=selected_med['dose'],
            lab=selected_lab['test']
        )
        note = ClinicalNote(appointment_id=appt.id, content=note_text)
        db.add(note)

        # 3. Billing — department-aware pricing, only for completed visits
        DEPT_BILLING = {
            "Emergency": (400, 1200), "Oncology": (600, 1800), "Cardiology": (300, 900),
            "Radiology": (200, 700), "Orthopedics": (250, 800), "Neurology": (250, 750),
            "Endocrinology": (150, 500), "Dermatology": (100, 400),
            "Pediatrics": (80, 350), "General Practice": (60, 250)
        }
        bill_min, bill_max = DEPT_BILLING.get(dept_name, (80, 600))
        billing = Billing(
            appointment_id=appt.id,
            amount=round(random.uniform(bill_min, bill_max), 2),
            status=random.choices(["Paid", "Pending"], weights=[70, 30], k=1)[0],
            payment_method=random.choice(["Credit Card", "Eftpos", "Insurance", "Cash"]),
            invoice_date=appt_date
        )
        db.add(billing)

        # 4. Prescription — same med as the note and diagnosis
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

        # 5. Lab Result — same lab as the condition's standard test
        if random.random() > 0.4:
            lab_def = selected_lab
            if random.random() > 0.8:  # 20% abnormal
                is_too_high = random.random() > 0.5
                val = lab_def['max'] + random.uniform(1.0, 10.0) if is_too_high else lab_def['min'] - random.uniform(1.0, 5.0)
                patient_risks[patient.id] += 15.0
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
    # Department-specific supplies — only mapped to departments that actually exist
    SUPPLY_MAP = {
        "Cardiology": ["ECG Electrodes", "Cardiac Stents", "Heart Valves", "Defibrillator Pads"],
        "Radiology": ["Contrast Agent", "Lead Aprons", "X-Ray Film"],
        "Emergency": ["Trauma Gauze", "IV Kits", "Defibrillator Pads", "Oxygen Masks"],
        "Oncology": ["Chemotherapy Bags", "IV Ports", "Antiemetic Kits"],
        "Endocrinology": ["Insulin Pens", "Blood Glucose Strips", "Saline Bags"],
        "Pediatrics": ["Paediatric Nebulisers", "Amoxicillin Suspension Stock"],
        "Neurology": ["EEG Electrodes", "Lumbar Puncture Kits"],
        "Orthopedics": ["Plaster of Paris Bandages", "Crutches", "Knee Braces"],
        "Dermatology": ["Biopsy Punch Kits", "Skin Stapler"],
        "General Practice": ["Blood Pressure Cuffs", "Tongue Depressors"]
    }
    # Universal supplies distributed to every department
    universal_items = ["Sterile Gauze", "Syringes (5ml)", "Nitrile Gloves", "Alcohol Swabs"]
    for dept in depts:
        dept_items = universal_items + SUPPLY_MAP.get(dept.name, [])
        for item in dept_items:
            s = MedicalSupply(
                item_name=item,
                quantity=random.randint(10, 200),
                reorder_level=random.randint(15, 30),
                supplier=fake.company(),
                department_id=dept.id,
                unit_cost=float(random.randint(1500, 5000)) if any(x in item for x in ["Stent", "Valve", "Stapler", "Kit", "Mask", "Nebuliser"]) else float(random.uniform(0.5, 50.0))
            )
            db.add(s)
    db.commit()

def recalculate_budgets(db: Session):
    print("Recalculating departmental budgets based on total expenses...")
    from sqlalchemy import func
    depts = db.query(Department).all()
    for dept in depts:
        # Sum up all staff salaries in this department using ORM
        total_salaries = db.query(func.sum(Staff.salary)).filter(Staff.department_id == dept.id).scalar() or 0
        
        # Estimate yearly supply spend (inventory value * 4 turns a year)
        inventory_value = db.query(func.sum(MedicalSupply.quantity * MedicalSupply.unit_cost)).filter(MedicalSupply.department_id == dept.id).scalar() or 0
        yearly_supplies = float(inventory_value) * 4
        
        # Smart Budget = (Salaries + Supplies) + 20% operating buffer, rounded to nearest 50k
        calculated_total = (float(total_salaries) + yearly_supplies) * 1.2
        smart_budget = round(calculated_total / 50000) * 50000
        dept.operating_budget = max(smart_budget, 500000.0)
    db.commit()

def seed_guidelines(db: Session):
    print("Seeding clinical guidelines...")
    guidelines = [
        {
            "title": "Cardiology Acute Response Policy",
            "category": "Cardiology",
            "content": "Any patient presenting with angina or unexplained palpitations must have an ECG performed immediately. If Troponin levels exceed 0.04 ng/mL, escalate to the attending Cardiologist and prepare for suspected Heart Failure or Atrial Fibrillation. Administer Warfarin cautiously for confirmed AFib. Monitor INR weekly."
        },
        {
            "title": "Pediatric Escalation Protocol",
            "category": "Pediatrics",
            "content": "For pediatric emergencies involving persistent wheezing, evaluate for Childhood Asthma immediately. Use a spacer for Salbutamol administration. If the patient has ear pain or suspected Tonsillitis, prescribe Amoxicillin Suspension and advise caretakers to keep it refrigerated and complete the full course."
        },
        {
            "title": "General Practice Viral Pathway",
            "category": "General Practice",
            "content": "Patients with a mild fever and persistent cough during winter months should be assessed for Influenza. A Full Blood Count may be necessary if symptoms persist beyond 5 days. Do not prescribe Amoxicillin for confirmed viral infections. Manage symptoms conservatively with hydration and rest."
        },
        {
            "title": "Emergency Trauma Handling",
            "category": "Emergency",
            "content": "In cases of acute trauma resulting in severe abdominal pain, suspect internal bleeding or Acute Appendicitis. STAT Morphine 5mg may be administered for pain control while monitoring respiratory rate. Tranexamic Acid 1g IV must be administered within 3 hours of injury for suspected internal haemorrhage. An urgent CT scan is mandatory."
        },
        {
            "title": "Endocrinology Diabetes Management",
            "category": "Endocrinology",
            "content": "All Type 2 Diabetes patients must have HbA1c monitored every 3 months. Metformin is the first-line treatment. Thyroid patients on Levothyroxine require TSH monitoring every 6 weeks until stable. Patients presenting with weight gain, facial rounding, and easy bruising should be screened for Cushing Syndrome."
        },
        {
            "title": "Oncology Chemotherapy Safety Protocol",
            "category": "Oncology",
            "content": "All patients receiving Cyclophosphamide must be pre-medicated with antiemetics. CEA Tumor Marker must be checked before each cycle. Rituximab infusions require pre-medication with antihistamine. ECOG performance status must be assessed before each cycle — pause treatment if ECOG exceeds Grade 2."
        }
    ]
    for g in guidelines:
        cg = ClinicalGuideline(**g)
        db.add(cg)
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
        recalculate_budgets(db)
        seed_guidelines(db)
        print("\n--- Clinical Simulation Seeding complete! ---")
        print("IMPORTANT: Run the vector embedding script next to embed the notes and guidelines.")
    finally:
        db.close()

if __name__ == "__main__":
    run_seeding()

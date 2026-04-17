import os
from datetime import datetime
import torch
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.models.clinical import ClinicalNote
from tqdm import tqdm

def run_embeddings():
    # 1. Initialize the local model
    print("Loading local AI model (BAAI/bge-m3)...")
    # This will download the model on the first run (roughly 1.2GB)
    model = SentenceTransformer('BAAI/bge-m3')
    
    # Use Metal (MPS) if available on Mac M5, otherwise CPU
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model.to(device)
    print(f"Using device: {device.upper()}")

    db = SessionLocal()
    try:
        from app.models.core import Patient, Department
        from app.models.clinical import Appointment
        
        # 2. Fetch notes that don't have vectors yet, with joined context
        notes_to_process = (
            db.query(ClinicalNote)
            .join(Appointment, ClinicalNote.appointment_id == Appointment.id)
            .join(Patient, Appointment.patient_id == Patient.id)
            .join(Department, Appointment.department_id == Department.id)
            .filter(ClinicalNote.vector == None)
            .all()
        )
        
        if not notes_to_process:
            print("No new clinical notes to process.")
            return

        print(f"Found {len(notes_to_process)} notes to encode with context.")
        
        # 3. Process in batches
        batch_size = 32
        for i in tqdm(range(0, len(notes_to_process), batch_size)):
            batch = notes_to_process[i:i + batch_size]
            
            # Build Contextual Strings for the vector model to "Understand"
            context_texts = []
            for note in batch:
                p = note.appointment.patient
                d = note.appointment.doctor.department
                
                # Calculate age
                age = (datetime.now().date() - p.date_of_birth).days // 365
                
                context_str = (
                    f"Patient: {p.first_name} {p.last_name} "
                    f"(Age: {age}, Gender: {p.gender}, Risk Profile: {p.risk_profile}). "
                    f"Dept: {d.name}. Note: {note.content}"
                )
                context_texts.append(context_str)
            
            # Generate vectors from the enriched context
            embeddings = model.encode(context_texts, convert_to_tensor=False)
            
            # Update objects
            for note, embedding in zip(batch, embeddings):
                note.vector = embedding.tolist()
            
            db.commit()
            
        print("\n--- AI Embedding Job Complete! ---")
        print(f"Successfully processed {len(notes_to_process)} clinical notes.")

    except Exception as e:
        print(f"Error during embedding generation: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_embeddings()

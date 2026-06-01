import os
import json
from datetime import datetime
import torch
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.models.clinical import ClinicalNote
from tqdm import tqdm

STATUS_FILE = "/tmp/embedding_status.json"

def write_status(status, done=0, total=0):
    try:
        with open(STATUS_FILE, "w") as f:
            json.dump({"status": status, "done": done, "total": total}, f)
    except Exception:
        pass

def run_embeddings():
    write_status("pending", 0, 0)
    db = SessionLocal()
    try:
        from app.models.core import Patient, Department
        from app.models.clinical import Appointment, ClinicalGuideline
        
        # 1. Fetch notes that don't have vectors yet
        notes_to_process = (
            db.query(ClinicalNote)
            .join(Appointment, ClinicalNote.appointment_id == Appointment.id)
            .join(Patient, Appointment.patient_id == Patient.id)
            .join(Department, Appointment.department_id == Department.id)
            .filter(ClinicalNote.vector == None)
            .all()
        )
        
        guidelines_to_process = db.query(ClinicalGuideline).filter(ClinicalGuideline.vector == None).all()

        total_to_process = len(notes_to_process) + len(guidelines_to_process)
        if total_to_process == 0:
            print("✅ All clinical data and guidelines already have embeddings. Skipping AI model load.")
            write_status("skipped", 0, 0)
            return

        # 2. ONLY NOW load the model (roughly 1.2GB)
        print("🧠 New notes found. Loading local AI model (BAAI/bge-m3)...")
        model = SentenceTransformer('BAAI/bge-m3')
        device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        model.to(device)
        print(f"Using device: {device.upper()}")
        
        if not notes_to_process:
            print("No new clinical notes to process.")
        else:
            print(f"Found {len(notes_to_process)} notes to encode with context.")
            
            # 3. Process in batches
            batch_size = 64
            total_batches = (len(notes_to_process) + batch_size - 1) // batch_size
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
                
                batch_index = i // batch_size + 1
                write_status("in_progress", min(batch_index, total_batches), total_batches)
                
            print(f"\nSuccessfully processed {len(notes_to_process)} clinical notes.")

        # --- Embed Clinical Guidelines ---
        guidelines_to_process = db.query(ClinicalGuideline).filter(ClinicalGuideline.vector == None).all()
        
        if guidelines_to_process:
            print(f"Found {len(guidelines_to_process)} guidelines to encode.")
            g_texts = [f"PROTOCOL: {g.title} (Category: {g.category}). {g.content}" for g in guidelines_to_process]
            g_embeddings = model.encode(g_texts, convert_to_tensor=False)
            
            for g, emb in zip(guidelines_to_process, g_embeddings):
                g.vector = emb.tolist()
            
            db.commit()
            print(f"Successfully processed {len(guidelines_to_process)} clinical guidelines.")
        
        write_status("complete", 1, 1)
        print("\n--- AI Embedding Job Complete! ---")

    except Exception as e:
        print(f"Error during embedding generation: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_embeddings()

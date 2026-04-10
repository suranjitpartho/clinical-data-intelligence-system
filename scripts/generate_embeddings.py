import os
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
        # 2. Fetch notes that don't have vectors yet
        notes_to_process = db.query(ClinicalNote).filter(ClinicalNote.vector == None).all()
        
        if not notes_to_process:
            print("No new clinical notes to process.")
            return

        print(f"Found {len(notes_to_process)} notes to encode.")
        
        # 3. Process in batches for efficiency
        batch_size = 32
        for i in tqdm(range(0, len(notes_to_process), batch_size)):
            batch = notes_to_process[i:i + batch_size]
            texts = [note.content for note in batch]
            
            # Generate vectors
            # bge-m3 normally outputs 1024 dimensions
            embeddings = model.encode(texts, convert_to_tensor=False)
            
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

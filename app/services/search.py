import torch
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.clinical import ClinicalNote
import numpy as np

# Load model once for the application
model = SentenceTransformer('BAAI/bge-m3')
device = "mps" if torch.backends.mps.is_available() else "cpu"
model.to(device)

def get_clinical_notes_semantic(db: Session, query: str, limit: int = 5):
    """
    Performs vector similarity search on clinical notes.
    """
    # 1. Generate embedding for the user query
    query_vector = model.encode(query, convert_to_tensor=False).tolist()
    
    # 2. Perform vector search using pgvector's L2 distance (<->) 
    # or Cosine similarity (<=>)
    # We'll use <=> because it works better for BGE models
    sql_query = text("""
        SELECT 
            cn.id, 
            cn.content, 
            cn.appointment_id,
            1 - (cn.vector <=> :query_vector) as similarity
        FROM clinical_notes cn
        ORDER BY cn.vector <=> :query_vector
        LIMIT :limit
    """)
    
    # Convert list to string format that pgvector expects: '[val1, val2...]'
    vector_str = f"[{','.join(map(str, query_vector))}]"
    
    results = db.execute(sql_query, {"query_vector": vector_str, "limit": limit}).fetchall()
    
    formatted_results = []
    for row in results:
        formatted_results.append({
            "content": row.content,
            "similarity": row.similarity,
            "appointment_id": str(row.appointment_id)
        })
        
    return formatted_results

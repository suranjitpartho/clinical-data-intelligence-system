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

def get_clinical_notes_semantic(db: Session, query: str, limit: int = 10):
    """
    Performs vector similarity search on clinical notes with full patient context.
    """
    # 1. Generate embedding for the user query
    query_vector = model.encode(query, convert_to_tensor=False).tolist()
    
    # 2. Perform vector search and join for context
    sql_query = text("""
        SELECT 
            cn.id, 
            cn.content, 
            p.first_name,
            p.last_name,
            p.risk_profile,
            d.name as dept_name,
            (CURRENT_DATE - p.date_of_birth) / 365 as age,
            1 - (cn.vector <=> :query_vector) as similarity
        FROM clinical_notes cn
        JOIN appointments a ON cn.appointment_id = a.id
        JOIN patients p ON a.patient_id = p.id
        JOIN departments d ON a.department_id = d.id
        ORDER BY cn.vector <=> :query_vector
        LIMIT :limit
    """)
    
    vector_str = f"[{','.join(map(str, query_vector))}]"
    results = db.execute(sql_query, {"query_vector": vector_str, "limit": limit}).fetchall()
    
    formatted_results = []
    for row in results:
        # Build a "Contextual Result" for the LLM to process
        context_preview = (
            f"[Patient: {row.first_name} {row.last_name}, Age: {int(row.age)}, "
            f"Risk: {row.risk_profile}, Dept: {row.dept_name}] "
            f"Note Content: {row.content}"
        )
        formatted_results.append({
            "content": context_preview,
            "similarity": float(row.similarity),
            "appointment_id": str(row.id)
        })
        
    return formatted_results

from app.db.base import SessionLocal
from app.services.search import get_clinical_notes_semantic

def test():
    db = SessionLocal()
    query = "patients with severe headache and fever"
    print(f"\nPerforming Semantic Search for: '{query}'...")
    
    results = get_clinical_notes_semantic(db, query)

    print("\n--- MATCHING CLINICAL NOTES ---")
    if not results:
        print("No results found.")
    for i, r in enumerate(results):
        print(f"{i+1}. [Similarity: {r['similarity']:.4f}]")
        print(f"   Content: {r['content']}")
        print(f"   Appt ID: {r['appointment_id']}\n")
    
    db.close()

if __name__ == "__main__":
    test()

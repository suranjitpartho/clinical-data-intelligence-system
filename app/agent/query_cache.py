from sqlalchemy import text
from app.db.base import SessionLocal
from app.models.cache import SemanticQueryCache
from app.services.search import model as embedding_model


# Look up a past query in the vector cache
def check_semantic_cache(query_text: str, threshold: float = 0.95):
    db = SessionLocal()
    try:
        query_vector = embedding_model.encode(query_text, convert_to_tensor=False).tolist()
        sql_query = text("""
            SELECT cached_sql, 1 - (vector <=> :query_vector) as similarity
            FROM semantic_query_cache
            ORDER BY vector <=> :query_vector
            LIMIT 1
        """)
        vector_str = f"[{','.join(map(str, query_vector))}]"
        result = db.execute(sql_query, {"query_vector": vector_str}).fetchone()
        if result and result.similarity >= threshold:
            return result.cached_sql, float(result.similarity)
        elif result:
            print(f"[CACHE MISS] Top similarity score: {result.similarity:.4f} (threshold: {threshold})")
    except Exception as e:
        db.rollback()
        print(f"Error checking semantic cache: {e}")
    finally:
        db.close()
    return None, None


# Save a new query and its SQL to the cache
def save_to_cache(query_text: str, cached_sql: str):
    db = SessionLocal()
    try:
        existing = db.query(SemanticQueryCache).filter(SemanticQueryCache.query_text == query_text).first()
        if existing:
            existing.cached_sql = cached_sql
            db.commit()
            return
        query_vector = embedding_model.encode(query_text, convert_to_tensor=False).tolist()
        cache_entry = SemanticQueryCache(
            query_text=query_text,
            vector=query_vector,
            cached_sql=cached_sql,
        )
        db.add(cache_entry)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error saving query to cache: {e}")
    finally:
        db.close()

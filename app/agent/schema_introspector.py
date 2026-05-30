"""
Schema Introspector: Reads FK relationships and column metadata directly from
PostgreSQL's information_schema. This ensures the AI always has an accurate,
up-to-date picture of join paths without any manual documentation.
"""
from functools import lru_cache
from sqlalchemy import text
from app.db.base import SessionLocal
from app.agent.exceptions import SchemaError


@lru_cache(maxsize=1)
def get_fk_relationship_map() -> str:
    """
    Queries information_schema to extract all FK relationships in the database.
    Returns a concise, human-readable string like:
      appointments.doctor_id  →  staff.id
      appointments.patient_id →  patients.id
    Cached so it only runs once per server lifetime.
    """
    sql = """
    SELECT
        kcu.table_name        AS from_table,
        kcu.column_name       AS from_column,
        ccu.table_name        AS to_table,
        ccu.column_name       AS to_column
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
       AND tc.table_schema    = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
       AND ccu.table_schema    = tc.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND tc.table_schema    = 'public'
    ORDER BY from_table, from_column;
    """
    session = SessionLocal()
    try:
        rows = session.execute(text(sql)).fetchall()
        if not rows:
            return "No foreign key relationships found."
        lines = [f"  {r.from_table}.{r.from_column}  →  {r.to_table}.{r.to_column}" for r in rows]
        return "\n".join(lines)
    except Exception as e:
        raise SchemaError(str(e)) from e
    finally:
        session.close()

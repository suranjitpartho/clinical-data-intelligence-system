import re
from sqlalchemy import text
from app.db.base import SessionLocal
from app.services.agent.state import AgentState
from app.services.query_cache import check_semantic_cache
from app.services.prompts import DATA_DICTIONARY_JSON

def cache_node(state: AgentState):
    db = SessionLocal()
    try:
        # Check cache using the rewritten query
        query = state["query"]
        cached_sql, similarity = check_semantic_cache(query, threshold=0.82)
        
        if not cached_sql:
            return {
                "cache_hit": False,
                "logs": "\n• Checking semantic query cache... Miss."
            }
            
        # Cache hit! Execute SQL directly to retrieve live results
        results = db.execute(text(cached_sql)).fetchall()
        raw_data = [dict(row._mapping) for row in results]
        
        # --- Automated Dimensional Enrichment ---
        reference_context = {}
        tables_found = re.findall(r'\b(?:FROM|JOIN)\s+([a-zA-Z0-9_]+)\b', cached_sql, re.IGNORECASE)
        for table in set(t.lower() for t in tables_found):
            table_meta = DATA_DICTIONARY_JSON.get(table)
            if table_meta and "reference_columns" in table_meta:
                ref_cols = ", ".join(table_meta["reference_columns"])
                ref_sql = f"SELECT DISTINCT {ref_cols} FROM {table}"
                try:
                    ref_res = db.execute(text(ref_sql)).fetchall()
                    reference_context[table] = [dict(r._mapping) for r in ref_res]
                except Exception:
                    continue
        
        total_count = len(raw_data)
        schema = list(raw_data[0].keys()) if raw_data else []
        display_data = raw_data[:25]
        
        metadata = {
            "total_count": total_count,
            "columns": schema,
            "truncated": total_count > 25
        }
        
        log_msg = (
            f"\n• Checking semantic query cache... **Hit** (Similarity: {similarity:.2%})!"
            f"\n• Reusing cached SQL query to bypass generation step."
        )
        
        return {
            "cache_hit": True,
            "tool_query": cached_sql,
            "data_results": display_data,
            "data_metadata": metadata,
            "reference_context": reference_context,
            "tools_needed": ["sql"],  # Log tool usage for audit logs
            "logs": log_msg
        }
    except Exception as e:
        print(f"Error in cache node execution: {e}")
        return {
            "cache_hit": False,
            "logs": f"\n• Checking semantic query cache... Error: {e}. Falling back to normal pipeline."
        }
    finally:
        db.close()

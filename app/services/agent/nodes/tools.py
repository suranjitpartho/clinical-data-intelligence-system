import json
import re
from sqlalchemy import text
from app.db.base import SessionLocal
from app.services.search import get_clinical_notes_semantic
from app.services.agent.state import AgentState
from app.services.schema_introspector import get_fk_relationship_map
from app.services.query_cache import save_to_cache
from app.services.refinement_utils import apply_data_refinement
from app.services.prompts import (
    SQL_GENERATION_PROMPT, 
    DISCOVERY_PROMPT, 
    DATA_DICTIONARY,
    DATA_DICTIONARY_JSON
)

def sql_node(state: AgentState, config, llm):
    query = state["query"]
    error_count = state.get("error_count", 0)
    session = SessionLocal() # Open fresh session for this node
    
    # --- Error Context Injection (Self-Correction) ---
    error_context = ""
    if error_count > 0 and state.get("tool_query") and "ERROR" in state["tool_query"]:
        previous_error = state["tool_query"]
        error_context = f"\n[PREVIOUS EXECUTION ERROR]:\nYou previously ran a query that resulted in this error. DO NOT make the same mistake. Fix the SQL syntax or logic based on this error message:\n{previous_error}\n"

    # --- Discovery Loop (Active Tool Execution) ---
    discovery_prompt = DISCOVERY_PROMPT.replace("{query}", query).replace("{schema}", DATA_DICTIONARY)
    discovery_res = llm.invoke(discovery_prompt, config).content
    
    discovery_context = "--- ACTUAL DATABASE CATEGORIES ---\n"
    try:
        # Parse the AI's discovery plan
        json_str = discovery_res.replace("```json", "").replace("```", "").strip()
        plan = json.loads(json_str)
        for item in plan.get("discovery_needed", []):
            t, c = item['table'], item['column']
            # Basic safety check
            if ";" in f"{t}{c}" or " " in f"{t}{c}": continue
            
            # Fetch REAL values from DB
            res = session.execute(text(f"SELECT DISTINCT {c} FROM {t} LIMIT 15")).fetchall()
            vals = [str(r[0]) for r in res if r[0] is not None]
            discovery_context += f"- Table '{t}', Column '{c}': Available values are {vals}\n"
    except Exception as e:
        discovery_context += f"Discovery failed: {e}\n"
    
    # --- Dynamic FK Relationship Map (auto-generated from DB schema) ---
    fk_map = get_fk_relationship_map()
    fk_context = f"\n[DATABASE FOREIGN KEY RELATIONSHIPS - Source of Truth for all JOINs]:\n{fk_map}\n"

    # We keep discovery_context for internal prompt use only, not for user logs
    sql_prompt = (
        SQL_GENERATION_PROMPT
        .replace("{query}", query)
        .replace("{discovery_context}", fk_context + discovery_context)
        .replace("{error_context}", error_context)
    )
    response_content = llm.invoke(sql_prompt, config).content.strip()

    # Extract reasoning thought block
    thought_block = ""
    if "<thought>" in response_content and "</thought>" in response_content:
        thought_block = response_content.split("<thought>")[1].split("</thought>")[0].strip()
    
    

    # 1. Precise Extraction: Split by the </thought> tag to isolate the code area
    if "</thought>" in response_content:
        potential_sql = response_content.split("</thought>")[-1].strip()
    else:
        potential_sql = response_content.strip()

    # Try markdown blocks within the potential SQL area first
    sql_blocks = re.findall(r'```(?:sql)?\n?(.*?)\n?```', potential_sql, re.DOTALL | re.IGNORECASE)
    if sql_blocks:
        sql = sql_blocks[-1].strip()
    else:
        sql = potential_sql.strip()

    # Final cleanup of any lingering backticks or bold markers
    sql = sql.replace("```sql", "").replace("```", "").strip()
    
    # --- Precise Code Isolation ---
    # Find the FIRST occurrence of WITH or SELECT that isn't preceded by letters (start of command)
    # We use a non-greedy catch-all to ensure we get the whole query
    match = re.search(r'\b(WITH|SELECT)\b', sql, re.IGNORECASE)
    if match:
        sql = sql[match.start():].strip()
    
    # Remove any trailing conversational text after the semicolon
    if ";" in sql:
        sql = sql.split(";")[0] + ";"
    
    # SAFETY NET: If the LLM completely failed to generate a SELECT query, stop here.
    if not sql.upper().startswith("SELECT") and not sql.upper().startswith("WITH"):
        session.close()  # FIX: close session to prevent connection leak
        return {
            "error_count": error_count + 1,
            "data_results": [],
            "data_metadata": {"total_count": 0, "columns": [], "error": "SQL_EXTRACTION_FAILED"},
            "tool_query": "ERROR: The AI failed to generate a valid SQL query.",
            "logs": "\nERROR: Could not isolate a valid SQL SELECT or WITH statement."
        }
    
    
    try:
        results = session.execute(text(sql)).fetchall()
        # Limit the data returned to the LLM for performance, but keep the total count
        raw_data = [dict(row._mapping) for row in results]
        
        # --- Automated Dimensional Enrichment ---
        reference_context = {}
        # Find tables mentioned in the SQL
        tables_found = re.findall(r'\b(?:FROM|JOIN)\s+([a-zA-Z0-9_]+)\b', sql, re.IGNORECASE)
        
        for table in set(t.lower() for t in tables_found):
            # Check if this table has reference columns defined in our Data Dictionary
            table_meta = DATA_DICTIONARY_JSON.get(table)
            if table_meta and "reference_columns" in table_meta:
                ref_cols = ", ".join(table_meta["reference_columns"])
                ref_sql = f"SELECT DISTINCT {ref_cols} FROM {table}"
                try:
                    ref_res = session.execute(text(ref_sql)).fetchall()
                    reference_context[table] = [dict(r._mapping) for r in ref_res]
                except Exception:
                    continue # Silently fail if ref query fails to avoid crashing main flow

        # --- Write to Semantic Query Cache ---
        try:
            save_to_cache(query, sql)
        except Exception as ce:
            print(f"Failed to cache generated SQL: {ce}")

        session.close() 
        
        # --- Structured Tool Response ---
        total_count = len(raw_data)
        schema = list(raw_data[0].keys()) if raw_data else []
        
        # We only pass a manageable subset to the synthesis layer
        display_data = raw_data[:25] 
        
        metadata = {
            "total_count": total_count,
            "columns": schema,
            "truncated": total_count > 25
        }
        
        final_trace = thought_block if thought_block else "Analyzing database for clinical patterns..."
        
        return {
            "data_results": display_data, 
            "data_metadata": metadata,
            "reference_context": reference_context, 
            "tool_query": sql, 
            "logs": "\n" + final_trace
        }
    except Exception as e:
        session.rollback()  # CRITICAL: Clean the transaction for the next nodes/logs
        session.close()
        
        # Keep trace clean—no SQL snippets, just user-friendly message
        error_msg = f"\n• Database query failed at attempt {error_count+1}\n• Refining approach and retrying..."
        
        # Explicitly inform the state of the failure
        return {
            "error_count": error_count + 1, 
            "data_results": [],
            "data_metadata": {"total_count": 0, "columns": [], "error": str(e)},
            "tool_query": f"ERROR: {str(e)}",
            "logs": error_msg
        }

def rag_node(state: AgentState):
    session = SessionLocal()
    search_query = state["query"]
    
    # Context Enrichment: If SQL already retrieved records, summarise them generically
    # to focus the vector search — no hardcoded field names, works for any table schema
    if state.get("data_results") and isinstance(state["data_results"], list):
        rows = state["data_results"][:5]
        row_snippets = []
        for row in rows:
            if isinstance(row, dict):
                # Serialize each row as "key: value" pairs, ignore nulls
                row_text = ", ".join(
                    f"{k}: {v}" for k, v in row.items() if v is not None
                )
                row_snippets.append(row_text)
        if row_snippets:
            search_query += f". Related records: {'; '.join(row_snippets[:3])[:300]}"

    data = get_clinical_notes_semantic(session, search_query)
    session.close()
    
    # Store unstructured text in medical_context
    context = [f"Record: {d['content']}" for d in data]
    
    print(f"[AGENT] RAG SUCCESS: Found {len(data)} results for query: {search_query[:50]}...")
    # Construct a professional clinical trace
    logs = (
        "\n• Initiating Semantic Search across clinical notes and institutional guidelines..."
        f"\n• Analyzing narrative patterns related to: '{search_query[:60]}...'"
        f"\n• Successfully retrieved {len(data)} relevant medical records for context synthesis."
    )

    return {
        "medical_context": context, 
        "logs": logs
    }

def refine_node(state: AgentState):
    """
    Refinement Node: Applies schema-agnostic deduplication, privacy filtering,
    and medical context filtering. Uses the reusable refinement utility.
    """
    data_results = state.get("data_results", [])
    metadata = state.get("data_metadata", {})
    
    if not data_results or not isinstance(data_results, list):
        return {}

    # 1. Apply core refinement logic (deduplication, ID/narrative filtering, metadata sync)
    refined_data, refined_metadata, refinement_log = apply_data_refinement(data_results, metadata)
    
    # 2. Filter medical_context based on refined_data
    medical_context = state.get("medical_context", [])
    filtered_medical_context = []
    context_logs = ""

    if medical_context and refined_data:
        # Extract identifiers from refined_data (names, MRN, NHI, etc.)
        # This needs to be robust and schema-agnostic
        identifiers = set()
        for row in refined_data:
            for k, v in row.items():
                if isinstance(v, str) and len(v) > 2:  # Avoid short, generic strings
                    k_lower = k.lower()
                    # Common identifier patterns, adjust as needed for your schema
                    if any(id_key in k_lower for id_key in ["name", "patient", "mrn", "nhi", "id"]):
                        identifiers.add(v.strip().lower())

        if identifiers:
            original_context_count = len(medical_context)
            for doc in medical_context:
                # Check if any identifier is present in the document content
                if any(ident in doc.lower() for ident in identifiers):
                    filtered_medical_context.append(doc)
            
            if len(filtered_medical_context) < original_context_count:
                context_logs = f"\n• Medical context refined: {len(filtered_medical_context)} relevant documents retained (from {original_context_count} raw documents)."
            else:
                context_logs = f"\n• Medical context validated: {len(filtered_medical_context)} documents verified."
        else:
            context_logs = "\n• No specific identifiers found in data_results to refine medical context."
            filtered_medical_context = medical_context # Keep original if no identifiers to filter by
    else:
        filtered_medical_context = medical_context # Keep original if no medical context or refined data

    # 3. Assemble final logs
    logs = f"\n• {refinement_log}" + context_logs

    return {
        "data_results": refined_data,
        "data_metadata": refined_metadata,
        "medical_context": filtered_medical_context,
        "logs": logs
    }

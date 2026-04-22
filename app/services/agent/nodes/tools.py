import json
import re
from sqlalchemy import text
from app.db.base import SessionLocal
from app.services.search import get_clinical_notes_semantic
from app.services.agent.state import AgentState
from app.services.prompts import (
    SQL_GENERATION_PROMPT, 
    DISCOVERY_PROMPT, 
    DATA_DICTIONARY
)

def sql_node(state: AgentState, llm):
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
    discovery_res = llm.invoke(discovery_prompt).content
    
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
    
    # We keep discovery_context for internal prompt use only, not for user logs
    sql_prompt = SQL_GENERATION_PROMPT.replace("{query}", query).replace("{discovery_context}", discovery_context).replace("{error_context}", error_context)
    response_content = llm.invoke(sql_prompt).content.strip()

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
        # Fallback: Find 'WITH' or 'SELECT' at the start of a line in the potential SQL area
        lines = potential_sql.split("\n")
        cleaned_lines = []
        found_start = False
        for line in lines:
            upper_line = line.strip().upper()
            if not found_start and (upper_line.startswith("SELECT ") or upper_line.startswith("WITH ")):
                found_start = True
            if found_start:
                cleaned_lines.append(line)
        sql = "\n".join(cleaned_lines).strip()
        
        # Final desperate fallback
        if not sql:
            sql_match = re.findall(r'(?:WITH|SELECT).*?;', potential_sql, re.DOTALL | re.IGNORECASE)
            if sql_match:
                sql = sql_match[-1].strip()
            else:
                sql = potential_sql
            
    # Final cleanup of any lingering backticks or bold markers
    sql = sql.replace("```sql", "").replace("```", "").strip()
    
    # Precise Trim: Ensure we don't have conversational headers before the code
    # We find the first line that contains our identified starting keyword
    sql_lines = sql.split("\n")
    cleaned_lines = []
    found_start = False
    for line in sql_lines:
        if not found_start and ("SELECT " in line.upper() or "WITH " in line.upper()):
            found_start = True
        if found_start:
            cleaned_lines.append(line)
    sql = "\n".join(cleaned_lines).strip()
    
    # SAFETY NET: If the LLM completely failed to generate a SELECT query, stop here.
    if not sql.upper().startswith("SELECT") and not sql.upper().startswith("WITH"):
        return {
            **state,
            "error_count": error_count + 1,
            "tool_query": "ERROR: The AI failed to generate a valid SQL query.",
            "logs": state.get("logs", "") + "\nERROR: Context window exhausted or LLM failed to output SQL."
        }
    
    
    try:
        results = session.execute(text(sql)).fetchall()
        data = [dict(row._mapping) for row in results]
        session.close() # Clean up
        
        # THE TRUE REASONING TRACE: Only show original reasoning to the user
        final_trace = thought_block if thought_block else "Analyzing database for clinical patterns..."
        
        return {
            **state, 
            "data_results": data, 
            "tool_query": sql, 
            "logs": final_trace
        }
    except Exception as e:
        session.rollback()  # CRITICAL: Clean the transaction for the next nodes/logs
        session.close()
        # Truncate large SQL in logs to keep the Reason Trace readable
        sql_snippet = sql[:200] + "..." if len(sql) > 200 else sql
        error_msg = f"\nERROR at attempt {error_count+1}: {str(e)[:150]}...\n[SQL Snippet]: {sql_snippet}"
        
        return {
            **state, 
            "error_count": error_count + 1, 
            "tool_query": f"ERROR: {str(e)}\nSQL attempt: {sql}",
            "logs": state.get("logs", "") + error_msg
        }

def rag_node(state: AgentState):
    session = SessionLocal()
    search_query = state["query"]
    
    # Context Injection (Context Collision Fix)
    # If SQL already found specific people, inject their names into the vector search
    if state.get("data_results") and isinstance(state["data_results"], list):
        names = []
        for row in state["data_results"]:
            if isinstance(row, dict):
                if "first_name" in row and "last_name" in row:
                    names.append(f"{row['first_name']} {row['last_name']}")
                elif "patient_name" in row:
                    names.append(str(row["patient_name"]))
        
        # Deduplicate and limit to prevent massive vector queries
        names = list(set(names))[:5]
        if names:
            search_query += f". Specific focus on patients: {', '.join(names)}"

    data = get_clinical_notes_semantic(session, search_query)
    session.close()
    
    # Store unstructured text in medical_context
    context = [f"Record: {d['content']}" for d in data]
    
    print(f"[AGENT] RAG SUCCESS: Found {len(data)} results for query: {search_query[:50]}...")
    return {
        **state, 
        "medical_context": context, 
        "tool_query": "Semantic Search on Clinical Notes",
        "logs": state.get("logs", "")
    }

def should_retry_sql(state: AgentState):
    if "ERROR" in (state["tool_query"] or "") and state["error_count"] < 2:
        return "retry"
    return "continue"

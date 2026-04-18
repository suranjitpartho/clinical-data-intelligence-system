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
    
    # Clean SQL: Strip thoughts and markdown blocks
    sql = response_content
    if "</thought>" in sql:
        sql = sql.split("</thought>")[-1].strip()
    sql = re.sub(r'```sql|```', '', sql).strip()
    
    try:
        results = session.execute(text(sql)).fetchall()
        data = [dict(row._mapping) for row in results]
        session.close() # Clean up
        
        # THE TRUE REASONING TRACE: Only show original reasoning to the user
        final_trace = thought_block if thought_block else "Analyzing database for clinical patterns..."
        
        print(f"[AGENT] SQL SUCCESS: Found {len(data)} results.")
        return {
            **state, 
            "data_results": data, 
            "tool_query": sql, 
            "logs": final_trace
        }
    except Exception as e:
        session.rollback()  # CRITICAL: Clean the transaction for the next nodes/logs
        session.close()
        print(f"[AGENT] SQL ERROR: {str(e)[:100]}...")
        return {
            **state, 
            "error_count": error_count + 1, 
            "tool_query": f"ERROR: {str(e)}\nSQL attempt: {sql}",
            "logs": state.get("logs", "") + f"\nERROR at attempt {error_count+1}: {str(e)}"
        }

def rag_node(state: AgentState):
    session = SessionLocal()
    data = get_clinical_notes_semantic(session, state["query"])
    session.close()
    
    # Store unstructured text in medical_context
    context = [f"Record: {d['content']}" for d in data]
    
    print(f"[AGENT] RAG SUCCESS: Found {len(data)} results.")
    return {
        **state, 
        "medical_context": context, 
        "tool_query": "Semantic Search on Clinical Notes",
        "logs": state.get("logs", "") + "\n--- Semantic Search Active ---"
    }

def should_retry_sql(state: AgentState):
    if "ERROR" in (state["tool_query"] or "") and state["error_count"] < 2:
        return "retry"
    return "continue"

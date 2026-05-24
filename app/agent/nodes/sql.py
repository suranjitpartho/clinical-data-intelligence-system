import json
import re
from sqlalchemy import text
from app.db.base import SessionLocal
from app.agent.state import AgentState
from app.agent.schema_introspector import get_fk_relationship_map
from app.agent.query_cache import save_to_cache
from app.services.refinement_utils import apply_data_refinement
from app.agent.prompts import (
    SQL_GENERATION_PROMPT,
    DISCOVERY_PROMPT,
    DATA_DICTIONARY,
    DATA_DICTIONARY_JSON,
)


def sql_node(state: AgentState, config, llm):
    query = state["query"]
    error_count = state.get("error_count", 0)
    session = SessionLocal()

    error_context = ""
    if error_count > 0 and state.get("tool_query") and "ERROR" in state["tool_query"]:
        raw = state["tool_query"]
        parts = raw.split("--- ATTEMPTED SQL ---\n", 1)
        error_msg = parts[0].replace("ERROR: ", "", 1).strip()
        attempted_sql = parts[1] if len(parts) > 1 else ""
        error_context = f"""
[PREVIOUS SQL ATTEMPT] - review what you wrote:
{attempted_sql}

[DATABASE ERROR] - what went wrong:
{error_msg}

[INSTRUCTION]:
Analyze the SQL above. Identify what caused the error.
Then write a complete, corrected SQL query that fixes the issue.
Do NOT repeat the same mistake. Start fresh.
"""

    discovery_prompt = DISCOVERY_PROMPT.replace("{query}", query).replace("{schema}", DATA_DICTIONARY)
    discovery_res = llm.invoke(discovery_prompt, config).content

    discovery_context = "--- ACTUAL DATABASE CATEGORIES ---\n"
    try:
        json_str = discovery_res.replace("```json", "").replace("```", "").strip()
        plan = json.loads(json_str)
        for item in plan.get("discovery_needed", []):
            t, c = item["table"], item["column"]
            if ";" in f"{t}{c}" or " " in f"{t}{c}":
                continue
            res = session.execute(text(f"SELECT DISTINCT {c} FROM {t} LIMIT 15")).fetchall()
            vals = [str(r[0]) for r in res if r[0] is not None]
            discovery_context += f"- Table '{t}', Column '{c}': Available values are {vals}\n"
    except Exception as e:
        discovery_context += f"Discovery failed: {e}\n"

    fk_map = get_fk_relationship_map()
    fk_context = f"\n[DATABASE FOREIGN KEY RELATIONSHIPS - Source of Truth for all JOINs]:\n{fk_map}\n"

    sql_prompt = (
        SQL_GENERATION_PROMPT.replace("{query}", query)
        .replace("{discovery_context}", fk_context + discovery_context)
        .replace("{error_context}", error_context)
    )
    response_content = llm.invoke(sql_prompt, config).content.strip()

    thought_block = ""
    if "<thought>" in response_content and "</thought>" in response_content:
        thought_block = response_content.split("<thought>")[1].split("</thought>")[0].strip()

    if "</thought>" in response_content:
        potential_sql = response_content.split("</thought>")[-1].strip()
    else:
        potential_sql = response_content.strip()

    sql_blocks = re.findall(r'```(?:sql)?\n?(.*?)\n?```', potential_sql, re.DOTALL | re.IGNORECASE)
    if sql_blocks:
        sql = sql_blocks[-1].strip()
    else:
        sql = potential_sql.strip()

    sql = sql.replace("```sql", "").replace("```", "").strip()

    match = re.search(r'\b(WITH|SELECT)\b', sql, re.IGNORECASE)
    if match:
        sql = sql[match.start():].strip()

    if ";" in sql:
        sql = sql.split(";")[0] + ";"

    sql = sql.replace("\\'", "'")

    if not sql.upper().startswith("SELECT") and not sql.upper().startswith("WITH"):
        session.close()
        return {
            "error_count": error_count + 1,
            "data_results": [],
            "data_metadata": {"total_count": 0, "columns": [], "error": "SQL_EXTRACTION_FAILED"},
            "tool_query": "ERROR: The AI failed to generate a valid SQL query.",
            "logs": "\nERROR: Could not isolate a valid SQL SELECT or WITH statement.",
        }

    try:
        results = session.execute(text(sql)).fetchall()
        raw_data = [dict(row._mapping) for row in results]

        reference_context = {}
        tables_found = re.findall(r'\b(?:FROM|JOIN)\s+([a-zA-Z0-9_]+)\b', sql, re.IGNORECASE)
        for table in set(t.lower() for t in tables_found):
            table_meta = DATA_DICTIONARY_JSON.get(table)
            if table_meta and "reference_columns" in table_meta:
                ref_cols = ", ".join(table_meta["reference_columns"])
                try:
                    ref_res = session.execute(text(f"SELECT DISTINCT {ref_cols} FROM {table}")).fetchall()
                    reference_context[table] = [dict(r._mapping) for r in ref_res]
                except Exception:
                    continue

        try:
            save_to_cache(query, sql)
        except Exception as ce:
            print(f"Failed to cache generated SQL: {ce}")

        session.close()

        total_count = len(raw_data)
        schema = list(raw_data[0].keys()) if raw_data else []
        display_data = raw_data[:25]

        final_trace = thought_block if thought_block else "Analyzing database for clinical patterns..."

        return {
            "data_results": display_data,
            "data_metadata": {
                "total_count": total_count,
                "columns": schema,
                "truncated": total_count > 25,
            },
            "reference_context": reference_context,
            "tool_query": sql,
            "logs": "\n" + final_trace,
        }
    except Exception as e:
        session.rollback()
        session.close()
        error_msg = f"\n• Database query failed at attempt {error_count+1}\n• Refining approach and retrying..."
        return {
            "error_count": error_count + 1,
            "data_results": [],
            "data_metadata": {"total_count": 0, "columns": [], "error": str(e)},
            "tool_query": f"ERROR: {str(e)}\n--- ATTEMPTED SQL ---\n{sql}",
            "logs": error_msg,
        }

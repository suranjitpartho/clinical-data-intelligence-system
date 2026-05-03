import json
from app.services.agent.state import AgentState
from app.services.prompts import SYNTHESIS_PROMPT

def format_as_markdown_table(data):
    if not data: return "No data available."
    columns = data[0].keys()
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = []
    for row in data:
        rows.append("| " + " | ".join(str(row.get(c, '')) for c in columns) + " |")
    return f"{header}\n{separator}\n" + "\n".join(rows)

def synthesis_node(state: AgentState, config, llm):
    metadata = state.get("data_metadata", {})
    data = state.get("data_results", [])
    
    # 1. Standardized Meta-Summary from the Source Tool
    total = metadata.get("total_count", 0)
    cols = ", ".join(metadata.get("columns", []))
    db_error = metadata.get("error")
    
    if db_error:
        meta_summary = f"DATASET AUDIT [FAILURE]: The database query failed with the following error: {db_error}. Please inform the user that a technical error occurred."
    else:
        meta_summary = f"DATASET AUDIT: Query returned {total} rows. Table Schema: [{cols}]."
        if metadata.get("truncated"):
            meta_summary += f" Note: displaying first 25 rows of {total} total."

    # 2. Markdown Formatting (Industry best practice for LLM data intake)
    markdown_data = format_as_markdown_table(data)
    
    synth_prompt = SYNTHESIS_PROMPT.format(
        query=state["query"], 
        tool_logic=state.get("tool_query", "No specific tool logic recorded."),
        meta_summary=meta_summary,
        data=markdown_data,
        medical_context="\n".join(state.get("medical_context", []))[:3000],
        reference_context=json.dumps(state.get("reference_context", {}), indent=2)
    )
    answer = llm.invoke(synth_prompt, config).content.replace("<|eot_id|>", "")
    return {"final_answer": answer}

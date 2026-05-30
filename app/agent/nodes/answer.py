import json
from langchain_core.messages import AIMessage
from app.agent.state import AgentState
from app.agent.prompts import SYNTHESIS_PROMPT


def format_as_markdown_table(data):
    if not data:
        return "No data available."
    columns = data[0].keys()
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = []
    for row in data:
        rows.append("| " + " | ".join(str(row.get(c, "")) for c in columns) + " |")
    return f"{header}\n{separator}\n" + "\n".join(rows)


async def synthesis_node(state: AgentState, config, llm):
    metadata = state.get("data_metadata", {})
    data = state.get("data_results", [])
    state_error = state.get("error")

    total = metadata.get("total_count", 0)
    cols = ", ".join(metadata.get("columns", []))
    db_error = metadata.get("error")

    if state_error:
        meta_summary = f"DATASET AUDIT [FAILURE]: The database query failed with the following error: {state_error.get('message', 'Unknown error')}. Please inform the user that a technical error occurred."
        medical_context = ""
    elif db_error:
        meta_summary = f"DATASET AUDIT [FAILURE]: The database query failed with the following error: {db_error}. Please inform the user that a technical error occurred."
        medical_context = ""
    else:
        meta_summary = f"DATASET AUDIT: Query returned {total} rows. Table Schema: [{cols}]."
        if metadata.get("truncated"):
            meta_summary += f" Note: displaying first 25 rows of {total} total."
        medical_context = "\n".join(state.get("medical_context", []))[:3000]

    markdown_data = format_as_markdown_table(data)

    synth_prompt = SYNTHESIS_PROMPT.format(
        query=state["query"],
        tool_logic=state.get("tool_query", "No specific tool logic recorded."),
        meta_summary=meta_summary,
        data=markdown_data,
        medical_context=medical_context,
        reference_context=json.dumps(state.get("reference_context", {}), indent=2),
    )
    chunks = []
    async for chunk in llm.astream(synth_prompt, config):
        chunks.append(chunk)
    full = "".join(c.content for c in chunks)
    answer = full.replace("<|eot_id|>", "")
    return {
        "final_answer": answer,
        "messages": [
            AIMessage(
                content=answer,
                additional_kwargs={
                    "data_results": state.get("data_results", []),
                    "tool_query": state.get("tool_query", ""),
                    "next_step": ", ".join(state.get("tools_needed", [])),
                },
            )
        ],
    }

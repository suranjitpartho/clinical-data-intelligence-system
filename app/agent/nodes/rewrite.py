from langchain_core.messages import HumanMessage
from app.agent.state import AgentState
from app.agent.exceptions import LLMProviderError
from app.agent.prompts import FOLLOW_UP_REWRITE_PROMPT


async def rewrite_node(state: AgentState, config, llm):
    msg_history = []
    for m in state.get("messages", [])[:-1]:
        role = "User" if isinstance(m, HumanMessage) else "Assistant"
        msg_history.append(f"{role}: {m.content}")

    history = msg_history[-5:]
    if not history:
        return {"logs": "\n• Identifying search intent..."}

    try:
        prompt = FOLLOW_UP_REWRITE_PROMPT.format(
            history="\n".join(history), query=state["query"]
        )
        response = await llm.ainvoke(prompt, config)
        rewritten_query = response.content.strip()
    except Exception as e:
        err = LLMProviderError(str(e), node="rewrite")
        return {
            "error": {"code": err.code, "message": str(e), "node": err.node, "recoverable": err.recoverable, "details": err.details},
            "logs": f"\n• Query rewrite failed: {e}",
        }

    if "REWRITTEN STANDALONE QUERY:" in rewritten_query.upper():
        rewritten_query = rewritten_query.split(":", 1)[-1].strip()

    logs_msg = f"\n• Query Rewritten: {rewritten_query}"
    if rewritten_query.lower() == state["query"].lower():
        logs_msg = "\n• New topic detected: Query not rewritten"

    return {"query": rewritten_query, "logs": logs_msg}

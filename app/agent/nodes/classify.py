from app.agent.state import AgentState
from app.agent.exceptions import LLMProviderError
from app.agent.prompts import INTENT_CLASSIFY_PROMPT


async def classify_node(state: AgentState, config, llm):
    try:
        prompt = INTENT_CLASSIFY_PROMPT.format(query=state["query"])
        response = (await llm.ainvoke(prompt, config)).content.strip().upper()
    except Exception as e:
        err = LLMProviderError(str(e), node="classify")
        return {
            "tools_needed": ["sql"],
            "error": {"code": err.code, "message": str(e), "node": err.node, "recoverable": err.recoverable, "details": err.details},
            "logs": f"\n• Intent classification failed: {e}. Defaulting to SQL.",
        }

    tools = [t.strip().lower() for t in response.split(",")]
    if "BOTH" in response:
        tools = ["sql", "rag"]

    return {"tools_needed": tools, "logs": f"\n• Active Tools: {', '.join(tools).upper()}"}

from app.agent.state import AgentState
from app.agent.prompts import INTENT_CLASSIFY_PROMPT


async def classify_node(state: AgentState, config, llm):
    prompt = INTENT_CLASSIFY_PROMPT.format(query=state["query"])
    response = (await llm.ainvoke(prompt, config)).content.strip().upper()

    tools = [t.strip().lower() for t in response.split(",")]
    if "BOTH" in response:
        tools = ["sql", "rag"]

    return {"tools_needed": tools, "logs": f"\n• Active Tools: {', '.join(tools).upper()}"}

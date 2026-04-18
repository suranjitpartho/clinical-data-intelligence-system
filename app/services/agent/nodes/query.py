from app.services.agent.state import AgentState
from app.services.prompts import FOLLOW_UP_REWRITE_PROMPT, INTENT_CLASSIFY_PROMPT

def rewrite_node(state: AgentState, llm):
    history = [f"{m['role']}: {m['content']}" for m in state.get("messages", [])[-5:]]
    if not history:
        return {**state, "logs": "--- FIRST QUERY: NO REWRITE NEEDED ---"}
    
    prompt = FOLLOW_UP_REWRITE_PROMPT.format(
        history="\n".join(history),
        query=state["query"]
    )
    rewritten_query = llm.invoke(prompt).content.strip()
    
    # Clean prefix if LLM hallucinates it
    if "REWRITTEN STANDALONE QUERY:" in rewritten_query.upper():
        rewritten_query = rewritten_query.split(":", 1)[-1].strip()
        
    logs_msg = f"--- QUERY REWRITTEN: {rewritten_query} ---"
    if rewritten_query.lower() == state["query"].lower():
        logs_msg = "--- NEW TOPIC DETECTED: QUERY NOT REWRITTEN ---"
        
    print(f"\n[AGENT] {logs_msg}")
    return {
        **state, 
        "query": rewritten_query, 
        "logs": logs_msg
    }

def intent_node(state: AgentState, llm):
    prompt = INTENT_CLASSIFY_PROMPT.format(query=state["query"])
    response = llm.invoke(prompt).content.strip().upper()
    
    # Parse potential multiple tools (e.g., "SQL,RAG")
    tools = [t.strip().lower() for t in response.split(",")]
    # Normalize "BOTH" if LLM returns it
    if "BOTH" in response:
        tools = ["sql", "rag"]
        
    print(f"[AGENT] INTENTS: {tools}")
    return {**state, "tools_needed": tools, "logs": f"--- INTENTS: {', '.join(tools).upper()} ---"}

from langchain_core.messages import HumanMessage, AIMessage
from app.services.agent.state import AgentState
from app.services.prompts import FOLLOW_UP_REWRITE_PROMPT, INTENT_CLASSIFY_PROMPT

def rewrite_node(state: AgentState, config, llm):
    # Extract text from LangChain message objects
    msg_history = []
    for m in state.get("messages", [])[:-1]: # Exclude the current query which was just added
        role = "User" if isinstance(m, HumanMessage) else "Assistant"
        msg_history.append(f"{role}: {m.content}")
    
    history = msg_history[-5:]
    if not history:
        return {"logs": "\n• Identifying search intent..."}
    
    prompt = FOLLOW_UP_REWRITE_PROMPT.format(
        history="\n".join(history),
        query=state["query"]
    )
    rewritten_query = llm.invoke(prompt, config).content.strip()
    
    # Clean prefix if LLM hallucinates it
    if "REWRITTEN STANDALONE QUERY:" in rewritten_query.upper():
        rewritten_query = rewritten_query.split(":", 1)[-1].strip()
        
    logs_msg = f"\n• Query Rewritten: {rewritten_query}"
    if rewritten_query.lower() == state["query"].lower():
        logs_msg = "\n• New topic detected: Query not rewritten"
        
    return {
        "query": rewritten_query, 
        "logs": logs_msg
    }

def intent_node(state: AgentState, config, llm):
    prompt = INTENT_CLASSIFY_PROMPT.format(query=state["query"])
    response = llm.invoke(prompt, config).content.strip().upper()
    
    # Parse potential multiple tools (e.g., "SQL,RAG")
    tools = [t.strip().lower() for t in response.split(",")]
    # Normalize "BOTH" if LLM returns it
    if "BOTH" in response:
        tools = ["sql", "rag"]
        
    return {"tools_needed": tools, "logs": f"\n• Active Tools: {', '.join(tools).upper()}"}

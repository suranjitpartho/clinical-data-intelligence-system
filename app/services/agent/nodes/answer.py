from app.services.agent.state import AgentState
from app.services.prompts import SYNTHESIS_PROMPT

def synthesis_node(state: AgentState, llm):
    synth_prompt = SYNTHESIS_PROMPT.format(
        query=state["query"], 
        data=str(state["data_results"])[:3000],
        medical_context="\n".join(state.get("medical_context", []))[:3000]
    )
    answer = llm.invoke(synth_prompt).content.replace("<|eot_id|>", "")
    return {**state, "final_answer": answer}

# Placeholder for future "Data Verification" Node
def verify_node(state: AgentState, llm):
    # This will be implemented next
    return state

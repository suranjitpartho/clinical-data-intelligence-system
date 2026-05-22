from app.services.agent.graph import ClinicalGraph

class CompatibilityAgent:
    async def invoke(self, state: dict):
        provider = state.get("provider")
        model_name = state.get("model")
        thread_id = state.get("thread_id", "default_session")
        history = state.get("history", [])
        
        agent = ClinicalGraph(provider=provider, model_name=model_name)
        return await agent.arun_query(state["query"], thread_id=thread_id, history=history)

clinical_agent = CompatibilityAgent()

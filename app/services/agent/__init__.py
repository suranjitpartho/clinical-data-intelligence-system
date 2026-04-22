from app.services.agent.graph import ClinicalGraph

# Dynamic Compatibility Interface
class CompatibilityAgent:
    def invoke(self, state: dict):
        provider = state.get("provider")
        model_name = state.get("model")
        thread_id = state.get("thread_id", "default_session")
        history = state.get("history", [])
        
        agent = ClinicalGraph(provider=provider, model_name=model_name)
        return agent.run_query(state["query"], thread_id=thread_id, history=history)

# Unified instance for the API
clinical_agent = CompatibilityAgent()

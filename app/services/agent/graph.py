from typing import List, Dict
from functools import partial
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.db.base import SessionLocal
from app.models.logs import AuditLog
from app.services.agent.state import AgentState
from app.services.agent.provider import get_llm

# Import nodes
from app.services.agent.nodes.query import rewrite_node, intent_node
from app.services.agent.nodes.tools import sql_node, rag_node
from app.services.agent.nodes.answer import synthesis_node

class ClinicalGraph:
    def __init__(self, provider=None, model_name=None):
        self.model_name = model_name or "default-model"
        self.llm = get_llm(provider, model_name)
        self.memory = MemorySaver()
        self.workflow = self._create_workflow()

    def route_from_classify(self, state: AgentState):
        tools = state.get("tools_needed", [])
        routes = []
        if "sql" in tools:
            routes.append("sql")
        if "rag" in tools:
            routes.append("rag")
        
        if not routes:
            return ["synthesis"]
        return routes

    def route_from_sql(self, state: AgentState):
        if "ERROR" in (state.get("tool_query") or "") and state.get("error_count", 0) < 2:
            return "retry"
        return "continue"

    def _create_workflow(self):
        graph = StateGraph(AgentState)
        
        # Add Nodes with explicit names for tracking
        graph.add_node("rewrite", lambda state, config: rewrite_node(state, config, self.llm))
        graph.add_node("classify", lambda state, config: intent_node(state, config, self.llm))
        graph.add_node("sql_tool", lambda state, config: sql_node(state, config, self.llm))
        graph.add_node("rag_tool", rag_node)
        graph.add_node("synthesis", lambda state, config: synthesis_node(state, config, self.llm))
        
        # Add Edges
        graph.set_entry_point("rewrite")
        graph.add_edge("rewrite", "classify")
        
        graph.add_conditional_edges(
            "classify",
            self.route_from_classify,
            {
                "sql": "sql_tool",
                "rag": "rag_tool",
                "synthesis": "synthesis"
            }
        )
        
        graph.add_conditional_edges(
            "sql_tool",
            self.route_from_sql,
            {
                "retry": "sql_tool",
                "continue": "synthesis"
            }
        )
        
        graph.add_edge("rag_tool", "synthesis")
        graph.add_edge("synthesis", END)
        
        return graph.compile(checkpointer=self.memory)

    def run_query(self, query: str, thread_id: str = "default", history: List[Dict] = None):
        db = SessionLocal()
        try:
            # Initialize Langfuse Callback if keys are available
            callbacks = []
            import os
            if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
                try:
                    from langfuse.langchain import CallbackHandler
                    langfuse_handler = CallbackHandler()
                    callbacks.append(langfuse_handler)
                except Exception as e:
                    print(f"Warning: Failed to initialize Langfuse callback: {e}")
            
            config = {
                "configurable": {"thread_id": thread_id}, 
                "callbacks": callbacks,
                "metadata": {
                    "source": os.getenv("ENV", "development"), 
                    "agent": "clinical-intelligence",
                    "model": self.model_name
                }
            }
            initial_state = {
                "query": query,
                "messages": history or [],
                "tools_needed": [],
                "tool_query": None,
                "data_results": [],
                "data_metadata": {},
                "medical_context": [],
                "final_answer": None,
                "error_count": 0,
                "logs": ""
            }
            
            final_output = self.workflow.invoke(initial_state, config=config)
            
            # Persist to Audit Log
            log = AuditLog(
                user_query=query,
                tool_used=", ".join(final_output.get("tools_needed", [])),
                tool_query=final_output.get("tool_query"),
                status="Success",
                result_summary=final_output["final_answer"][:500] if final_output["final_answer"] else "Complete"
            )
            db.add(log)
            db.commit()
            
            # Update history for the return
            new_messages = (history or []) + [
                {"role": "user", "content": query},
                {"role": "assistant", "content": final_output["final_answer"]}
            ]
            
            if callbacks:
                try:
                    callbacks[0].flush()
                except Exception:
                    pass
            
            return {
                "final_answer": final_output["final_answer"],
                "next_step": ", ".join(final_output.get("tools_needed", [])),
                "data_results": final_output["data_results"],
                "medical_context": final_output.get("medical_context", []),
                "tool_query": final_output.get("tool_query"),
                "logs": final_output["logs"],
                "history": new_messages,
                "is_error": False
            }
        except Exception as e:
            error_msg = str(e)
            # Handle Rate Limits (Groq/OpenAI/Anthropic)
            if "429" in error_msg or "rate limit" in error_msg.lower():
                friendly_msg = (
                    "**Model Rate Limit Reached**: The current AI model has reached its daily or minute-level token limit. "
                    "To continue your analysis without interruption, please switch to a different model or provider using the selection menu at the bottom of the left sidebar."
                )
                return {
                    "final_answer": friendly_msg, 
                    "data_results": [],
                    "logs": f"Technical Details: {error_msg}",
                    "is_error": True
                }
            
            return {"final_answer": f"Graph Error: {error_msg}", "data_results": [], "is_error": True}
        finally:
            db.close()

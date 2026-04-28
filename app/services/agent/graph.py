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
from app.services.agent.nodes.tools import sql_node, rag_node, should_retry_sql
from app.services.agent.nodes.answer import synthesis_node

class ClinicalGraph:
    def __init__(self, provider=None, model_name=None):
        self.llm = get_llm(provider, model_name)
        self.memory = MemorySaver()
        self.workflow = self._create_workflow()

    def route_from_classify(self, state: AgentState):
        tools = state.get("tools_needed", [])
        if "sql" in tools:
            return "sql"
        if "rag" in tools:
            return "rag"
        return "synthesis"

    def route_from_sql(self, state: AgentState):
        if "ERROR" in (state.get("tool_query") or "") and state.get("error_count", 0) < 2:
            return "retry"
        if "rag" in state.get("tools_needed", []):
            return "rag"
        return "continue"

    def _create_workflow(self):
        graph = StateGraph(AgentState)
        
        # Add Nodes with LLM dependency injected where needed
        graph.add_node("rewrite", partial(rewrite_node, llm=self.llm))
        graph.add_node("classify", partial(intent_node, llm=self.llm))
        graph.add_node("sql_tool", partial(sql_node, llm=self.llm))
        graph.add_node("rag_tool", rag_node)
        graph.add_node("synthesis", partial(synthesis_node, llm=self.llm))
        
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
                "rag": "rag_tool",
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
            
            config = {"configurable": {"thread_id": thread_id}, "callbacks": callbacks}
            initial_state = {
                "query": query,
                "messages": history or [],
                "tools_needed": [],
                "tool_query": None,
                "data_results": [],
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
            
            return {
                "final_answer": final_output["final_answer"],
                "next_step": ", ".join(final_output.get("tools_needed", [])),
                "data_results": final_output["data_results"],
                "medical_context": final_output.get("medical_context", []),
                "logs": final_output["logs"],
                "history": new_messages
            }
        except Exception as e:
            return {"final_answer": f"Graph Error: {str(e)}", "data_results": []}
        finally:
            if 'callbacks' in locals() and callbacks:
                try:
                    callbacks[0].flush()
                except Exception:
                    pass
            db.close()

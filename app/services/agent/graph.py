import inspect
import datetime
from typing import List, Dict
from langgraph.graph import StateGraph, START, END
from app.services.agent.checkpointer import get_checkpointer

from sqlalchemy import text
from app.db.base import SessionLocal
from app.models.logs import AuditLog
from langchain_core.messages import HumanMessage, AIMessage
from app.services.agent.state import AgentState
from app.services.agent.provider import get_llm

# Import nodes
from app.services.agent.nodes.query import rewrite_node, intent_node
from app.services.agent.nodes.tools import sql_node, rag_node, refine_node
from app.services.agent.nodes.answer import synthesis_node
from app.services.agent.nodes.cache import cache_node


def _bind_llm(fn, llm):
    """Wrap a node function with the LLM, preserving sync/async signature."""
    if inspect.iscoroutinefunction(fn):
        async def wrapper(state, config):
            return await fn(state, config, llm)
    else:
        def wrapper(state, config):
            return fn(state, config, llm)
    wrapper.__name__ = fn.__name__
    return wrapper


class ClinicalGraph:
    def __init__(self, provider=None, model_name=None):
        self.model_name = model_name or "default-model"
        self.llm = get_llm(provider, model_name)
        self.memory = get_checkpointer()
        self.workflow = self._create_workflow()

    def route_from_cache(self, state: AgentState):
        if state.get("cache_hit"):
            return "synthesis"
        return "classify"

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
        return "refine"

    def _create_workflow(self):
        graph = StateGraph(AgentState)
        
        # Add Nodes with explicit names for tracking
        graph.add_node("rewrite", _bind_llm(rewrite_node, self.llm))
        graph.add_node("cache_check", cache_node)
        graph.add_node("classify", _bind_llm(intent_node, self.llm))
        graph.add_node("sql_tool", _bind_llm(sql_node, self.llm))
        graph.add_node("rag_tool", rag_node)
        graph.add_node("refine", refine_node)
        graph.add_node("synthesis", _bind_llm(synthesis_node, self.llm))
        
        # Add Edges
        graph.add_edge(START, "rewrite")
        graph.add_edge("rewrite", "cache_check")
        
        graph.add_conditional_edges(
            "cache_check",
            self.route_from_cache,
            {
                "synthesis": "synthesis",
                "classify": "classify"
            }
        )
        
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
                "refine": "refine"
            }
        )
        
        graph.add_edge("rag_tool", "refine")
        graph.add_edge("refine", "synthesis")
        graph.add_edge("synthesis", END)
        
        return graph.compile(checkpointer=self.memory)

    async def arun_query(self, query: str, thread_id: str = "default", history: List[Dict] = None):
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
                    "model": self.model_name,
                    "langfuse_session_id": thread_id,
                    "langfuse_tags": ["clinical-intelligence", self.model_name]
                }
            }

            # Check if thread already has checkpoints (existing conversation)
            existing = db.execute(
                text("SELECT 1 FROM checkpoints WHERE thread_id = :tid LIMIT 1"),
                {"tid": thread_id}
            ).fetchone()

            if existing:
                # Resume existing thread — preserve thread_title and created_at
                # from the latest checkpoint metadata
                existing_meta = db.execute(
                    text("SELECT metadata FROM checkpoints WHERE thread_id = :tid ORDER BY checkpoint_id DESC LIMIT 1"),
                    {"tid": thread_id}
                ).scalar()
                if existing_meta:
                    config["metadata"]["thread_title"] = existing_meta.get("thread_title", "Untitled")
                    config["metadata"]["created_at"] = existing_meta.get("created_at")

                input_state = {
                    "query": query,
                    "messages": [HumanMessage(content=query)],
                }
            else:
                # New thread — store title + timestamp in metadata for sidebar
                config["metadata"]["thread_title"] = (
                    history[0]["content"][:80] if history else query[:80]
                )
                config["metadata"]["created_at"] = datetime.datetime.now(
                    datetime.timezone.utc
                ).isoformat()

                message_history = []
                if history:
                    for m in history:
                        if m["role"] == "user":
                            message_history.append(HumanMessage(content=m["content"]))
                        elif m["role"] == "assistant":
                            message_history.append(AIMessage(content=m["content"]))

                input_state = {
                    "query": query,
                    "messages": message_history + [HumanMessage(content=query)],
                    "tools_needed": [],
                    "tool_query": None,
                    "data_results": [],
                    "data_metadata": {},
                    "medical_context": [],
                    "final_answer": None,
                    "error_count": 0,
                    "logs": "",
                    "cache_hit": None
                }
            
            final_output = await self.workflow.ainvoke(input_state, config=config)
            
            # Determine success/failure status dynamically
            tool_query = final_output.get("tool_query")
            status = "Success"
            if (tool_query and "ERROR" in tool_query) or final_output.get("is_error"):
                status = "Error"

            # Proactively update Langfuse trace level if it failed
            if status == "Error" and callbacks:
                try:
                    trace_id = callbacks[0].get_trace_id()
                    if trace_id:
                        callbacks[0].langfuse.trace(
                            id=trace_id,
                            level="ERROR",
                            status_message=tool_query or "Query execution failed."
                        )
                except Exception as le:
                    print(f"Warning: Failed to update Langfuse trace level: {le}")
            
            # Persist to Audit Log
            log = AuditLog(
                user_query=query,
                tool_used=", ".join(final_output.get("tools_needed", [])),
                tool_query=tool_query,
                status=status,
                result_summary=final_output["final_answer"][:500] if final_output["final_answer"] else "Complete"
            )
            db.add(log)
            db.commit()
            
            # Convert history for the return (back to dicts for frontend)
            new_messages = []
            for m in final_output["messages"]:
                role = "user" if isinstance(m, HumanMessage) else "assistant"
                new_messages.append({"role": role, "content": m.content})
            
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
            import traceback
            error_msg = str(e)
            print(f"arun_query error [{type(e).__name__}]: {error_msg}")
            traceback.print_exc()
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
            
            return {"final_answer": f"Graph Error ({type(e).__name__}): {error_msg}", "data_results": [], "is_error": True}
        finally:
            db.close()

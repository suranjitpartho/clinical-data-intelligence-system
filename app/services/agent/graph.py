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
            lambda x: x["tool_used"],
            {
                "sql": "sql_tool",
                "rag": "rag_tool"
            }
        )
        
        graph.add_conditional_edges(
            "sql_tool",
            should_retry_sql,
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
            config = {"configurable": {"thread_id": thread_id}}
            initial_state = {
                "query": query,
                "messages": history or [],
                "tool_used": None,
                "tool_query": None,
                "data_results": [],
                "final_answer": None,
                "error_count": 0,
                "logs": ""
            }
            
            final_output = self.workflow.invoke(initial_state, config=config)
            
            # Persist to Audit Log
            log = AuditLog(
                user_query=query,
                tool_used=final_output["tool_used"],
                tool_query=final_output["tool_query"],
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
                "next_step": final_output["tool_used"],
                "data_results": final_output["data_results"],
                "logs": final_output["logs"],
                "history": new_messages
            }
        except Exception as e:
            return {"final_answer": f"Graph Error: {str(e)}", "data_results": []}
        finally:
            db.close()

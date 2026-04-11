import os
import json
import re
import typing
from typing import Annotated, List, Dict, Optional
import typing_extensions
from typing_extensions import TypedDict

# Python 3.9 + Pydantic 2 Compatibility Patch
if not hasattr(typing, "_TypedDictMeta"):
    typing.TypedDict = TypedDict

from datetime import datetime
from sqlalchemy import text
from langgraph.graph import StateGraph, END

from app.db.base import SessionLocal
from app.services.search import get_clinical_notes_semantic
from app.models.logs import AuditLog
from app.services.prompts import (
    SQL_GENERATION_PROMPT, 
    INTENT_CLASSIFY_PROMPT, 
    SYNTHESIS_PROMPT, 
    DISCOVERY_PROMPT, 
    DATA_DICTIONARY, 
    REASONING_PROMPT
)

# 1. State Definition
class AgentState(TypedDict):
    query: str
    tool_used: Optional[str]
    tool_query: Optional[str]
    data_results: List[Dict]
    final_answer: Optional[str]
    error_count: int
    logs: str
    db_session: any

# 1. Provide-Agnostic LLM Switcher (Dynamic)
def get_llm(provider=None, model_name=None):
    provider = (provider or os.getenv("AI_PROVIDER", "groq")).lower()
    model_name = model_name or os.getenv("AI_MODEL", "llama-3.3-70b-versatile")
    
    if provider == "mlx-server":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name, 
            temperature=0, 
            api_key="not-needed",
            base_url="http://127.0.0.1:8080/v1",
            timeout=30,
            max_tokens=2048,
            stop=["<|eot_id|>"]
        )
    elif provider == "groq":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name, 
            temperature=0, 
            openai_api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model_name, temperature=0, api_key=os.getenv("AI_API_KEY"))
    
    # Default fallback
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model=model_name, temperature=0, api_key=os.getenv("AI_API_KEY"))

class ClinicalGraph:
    def __init__(self, provider=None, model_name=None):
        self.llm = get_llm(provider, model_name)
        self.workflow = self._create_workflow()

    def _create_workflow(self):
        graph = StateGraph(AgentState)
        
        # Add Nodes
        graph.add_node("classify", self.intent_node)
        graph.add_node("sql_tool", self.sql_node)
        graph.add_node("rag_tool", self.rag_node)
        graph.add_node("synthesis", self.synthesis_node)
        
        # Add Edges
        graph.set_entry_point("classify")
        
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
            self.should_retry_sql,
            {
                "retry": "sql_tool",
                "continue": "synthesis"
            }
        )
        
        graph.add_edge("rag_tool", "synthesis")
        graph.add_edge("synthesis", END)
        
        return graph.compile()

    # --- NODE: Intent Classification ---
    def intent_node(self, state: AgentState):
        prompt = INTENT_CLASSIFY_PROMPT.format(query=state["query"])
        response = self.llm.invoke(prompt).content.strip().lower()
        tool = "sql" if "sql" in response else "rag"
        return {**state, "tool_used": tool, "logs": f"--- INTENT: {tool.upper()} ---"}

    # --- NODE: SQL Operations ---
    def sql_node(self, state: AgentState):
        query = state["query"]
        error_count = state.get("error_count", 0)
        
        # --- Discovery Loop (Active Tool Execution) ---
        discovery_prompt = DISCOVERY_PROMPT.replace("{query}", query).replace("{schema}", DATA_DICTIONARY)
        discovery_res = self.llm.invoke(discovery_prompt).content
        
        discovery_context = "--- ACTUAL DATABASE CATEGORIES ---\n"
        try:
            # Parse the AI's discovery plan
            json_str = discovery_res.replace("```json", "").replace("```", "").strip()
            plan = json.loads(json_str)
            for item in plan.get("discovery_needed", []):
                t, c = item['table'], item['column']
                # Basic safety check
                if ";" in f"{t}{c}" or " " in f"{t}{c}": continue
                
                # Fetch REAL values from DB
                res = state["db_session"].execute(text(f"SELECT DISTINCT {c} FROM {t} LIMIT 15")).fetchall()
                vals = [str(r[0]) for r in res if r[0] is not None]
                discovery_context += f"- Table '{t}', Column '{c}': Available values are {vals}\n"
        except Exception as e:
            discovery_context += f"Discovery failed: {e}\n"

        sql_prompt = SQL_GENERATION_PROMPT.replace("{query}", query).replace("{discovery_context}", discovery_context)
        sql = self.llm.invoke(sql_prompt).content.strip()

        # Clean SQL: Strip thoughts and markdown blocks
        if "</thought>" in sql:
            sql = sql.split("</thought>")[-1].strip()
        sql = re.sub(r'```sql|```', '', sql).strip()
        
        try:
            results = state["db_session"].execute(text(sql)).fetchall()
            data = [dict(row._mapping) for row in results]
            return {
                **state, 
                "data_results": data, 
                "tool_query": sql, 
                "logs": state["logs"] + f"\nSQL: {sql}"
            }
        except Exception as e:
            state["db_session"].rollback()  # CRITICAL: Clean the transaction for the next nodes/logs
            return {
                **state, 
                "error_count": error_count + 1, 
                "tool_query": f"ERROR: {str(e)}\nSQL attempt: {sql}",
                "logs": state["logs"] + f"\nERROR at attempt {error_count+1}: {str(e)}"
            }

    def should_retry_sql(self, state: AgentState):
        if "ERROR" in (state["tool_query"] or "") and state["error_count"] < 2:
            return "retry"
        return "continue"

    # --- NODE: RAG Operations ---
    def rag_node(self, state: AgentState):
        data = get_clinical_notes_semantic(state["db_session"], state["query"])
        return {
            **state, 
            "data_results": data, 
            "tool_query": "Semantic Search on Clinical Notes",
            "logs": state["logs"] + "\n--- Semantic Search Active ---"
        }

    # --- NODE: Synthesis ---
    def synthesis_node(self, state: AgentState):
        synth_prompt = SYNTHESIS_PROMPT.format(
            query=state["query"], 
            data=str(state["data_results"])[:4000]
        )
        answer = self.llm.invoke(synth_prompt).content.replace("<|eot_id|>", "")
        return {**state, "final_answer": answer}

    def run_query(self, query: str):
        db = SessionLocal()
        try:
            initial_state = {
                "query": query,
                "tool_used": None,
                "tool_query": None,
                "data_results": [],
                "final_answer": None,
                "error_count": 0,
                "logs": "",
                "db_session": db
            }
            
            final_output = self.workflow.invoke(initial_state)
            
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
            
            return {
                "final_answer": final_output["final_answer"],
                "next_step": final_output["tool_used"],
                "data_results": final_output["data_results"]
            }
        except Exception as e:
            return {"final_answer": f"Graph Error: {str(e)}", "data_results": []}
        finally:
            db.close()

# Dynamic Compatibility Interface
class CompatibilityAgent:
    def invoke(self, state: dict):
        provider = state.get("provider")
        model_name = state.get("model")
        agent = ClinicalGraph(provider=provider, model_name=model_name)
        return agent.run_query(state["query"])

clinical_agent = CompatibilityAgent()

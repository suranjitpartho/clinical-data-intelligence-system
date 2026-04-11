import os
import json
import re
from datetime import datetime
from sqlalchemy import text
from app.db.base import SessionLocal
from app.services.search import get_clinical_notes_semantic
from app.models.logs import AuditLog
from app.services.prompts import SQL_GENERATION_PROMPT, INTENT_CLASSIFY_PROMPT, SYNTHESIS_PROMPT, DISCOVERY_PROMPT, DATA_DICTIONARY, REASONING_PROMPT

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

class ClinicalAgent:
    def __init__(self, provider=None, model_name=None):
        self.llm = get_llm(provider, model_name)

    def classify_intent(self, query: str) -> str:
        prompt = INTENT_CLASSIFY_PROMPT.format(query=query)
        response = self.llm.invoke(prompt)
        return response.content.replace("<|eot_id|>", "").strip().upper()

    def discover_values(self, query: str, db) -> str:
        discovery_prompt = DISCOVERY_PROMPT.replace("{schema}", DATA_DICTIONARY).replace("{query}", query)
        response = self.llm.invoke(discovery_prompt).content
        
        try:
            json_str = response.replace("```json", "").replace("```", "").replace("<|eot_id|>", "").strip()
            data = json.loads(json_str)
            needed = data.get("discovery_needed", [])
            
            if not needed:
                return "Standard query; no categorical discovery needed."
            
            context = "REAL DATABASE VALUES FOR REFERENCE:\n"
            for item in needed:
                table = item['table']
                col = item['column']
                if " " in f"{table}{col}" or ";" in f"{table}{col}": continue
                
                res = db.execute(text(f"SELECT DISTINCT {col} FROM {table} LIMIT 20")).fetchall()
                values = [str(row[0]) for row in res if row[0] is not None]
                context += f"- In table '{table}', column '{col}' contains these actual values: {values}\n"
            return context
        except Exception as e:
            return f"Discovery skipped: {str(e)}"

    def generate_sql(self, query: str, discovery_context: str = "") -> str:
        prompt = SQL_GENERATION_PROMPT.replace("{query}", query).replace("{discovery_context}", discovery_context)
        response = self.llm.invoke(prompt).content
        
        sql = response.replace("<|eot_id|>", "").strip()
        match = re.search(r'^\s*(WITH|SELECT)\b.*?;', sql, re.DOTALL | re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(0).strip()
        return sql.strip()

    def run_query(self, query: str) -> dict:
        intent = self.classify_intent(query)
        tool_used = "SQL" if "SQL" in intent else "RAG"
        
        db = SessionLocal()
        final_data = []
        full_log = ""
        
        try:
            if tool_used == "SQL":
                discovery_context = self.discover_values(query, db)
                sql = self.generate_sql(query, discovery_context)
                results = db.execute(text(sql)).fetchall()
                data = [dict(row._mapping) for row in results]
                final_data.extend(data)
                full_log += f"--- STEP 1 DISCOVERY ---\n{discovery_context}\n\n--- STEP 1 SQL ---\n{sql}\n\n"
                
                if data:
                    reason_prompt = REASONING_PROMPT.format(query=query, data=str(data)[:2000])
                    follow_up = self.llm.invoke(reason_prompt).content.strip()
                    if "COMPLETE" not in follow_up.upper() and len(follow_up) > 5:
                        discovery_context_2 = self.discover_values(follow_up, db)
                        sql_2 = self.generate_sql(follow_up, discovery_context_2)
                        results_2 = db.execute(text(sql_2)).fetchall()
                        data_2 = [dict(row._mapping) for row in results_2]
                        final_data.extend(data_2)
                        full_log += f"--- STEP 2 (Deep Dive: {follow_up}) ---\n{discovery_context_2}\n\n--- STEP 2 SQL ---\n{sql_2}"
            else:
                final_data = get_clinical_notes_semantic(db, query)
                full_log = f"RAG Query: {query}"

            synth_prompt = SYNTHESIS_PROMPT.format(query=query, data=str(final_data)[:4000])
            final_answer = self.llm.invoke(synth_prompt).content.replace("<|eot_id|>", "")

            log = AuditLog(
                user_query=query,
                tool_used=tool_used,
                tool_query=full_log,
                status="Success",
                result_summary=final_answer[:500] if final_answer else "Analysis Complete"
            )
            db.add(log)
            db.commit()

            return {
                "final_answer": final_answer,
                "next_step": tool_used,
                "data_results": final_data
            }
        except Exception as e:
            db.rollback()
            return {"final_answer": f"Error: {str(e)}", "next_step": "Error", "data_results": []}
        finally:
            db.close()

# Dynamic Compatibility Interface
class CompatibilityAgent:
    def invoke(self, state: dict):
        provider = state.get("provider")
        model_name = state.get("model")
        agent = ClinicalAgent(provider=provider, model_name=model_name)
        return agent.run_query(state["query"])

clinical_agent = CompatibilityAgent()

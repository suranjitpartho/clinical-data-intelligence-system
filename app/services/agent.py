import os
import json
from datetime import datetime
from sqlalchemy import text
from app.db.base import SessionLocal
from app.services.search import get_clinical_notes_semantic
from app.models.logs import AuditLog
from app.services.prompts import SQL_GENERATION_PROMPT, INTENT_CLASSIFY_PROMPT, SYNTHESIS_PROMPT, DISCOVERY_PROMPT, DATA_DICTIONARY

# 1. Provide-Agnostic LLM Switcher
def get_llm():
    provider = os.getenv("AI_PROVIDER", "mlx-server").lower()
    model_name = os.getenv("AI_MODEL", "mlx-community/Meta-Llama-3-8B-Instruct-4bit")
    
    if provider == "mlx-server":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name, 
            temperature=0, 
            api_key="not-needed",
            base_url="http://127.0.0.1:8080/v1",
            max_retries=0,
            timeout=30,
            max_tokens=500,
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
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model_name, temperature=0, anthropic_api_key=os.getenv("AI_API_KEY"))
    
    # Fallback to MLX
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=model_name, 
        temperature=0, 
        api_key="not-needed",
        base_url="http://127.0.0.1:8080/v1",
        max_retries=0,
        timeout=30,
        max_tokens=500,
        stop=["<|eot_id|>"]
    )

llm = get_llm()

class ClinicalAgent:
    """
    A robust, library-agnostic agent that orchestrates clinical intelligence.
    """
    def classify_intent(self, query: str) -> str:
        prompt = INTENT_CLASSIFY_PROMPT.format(query=query)
        response = llm.invoke(prompt)
        return response.content.replace("<|eot_id|>", "").strip().upper()

    def discover_values(self, query: str, db) -> str:
        """
        Scan the DB for actual categorical values before generating the final SQL.
        """
        discovery_prompt = DISCOVERY_PROMPT.replace("{schema}", DATA_DICTIONARY).replace("{query}", query)
        response = llm.invoke(discovery_prompt).content
        
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
                # Basic safety check (ensure no spaces in table/col names)
                if " " in f"{table}{col}" or ";" in f"{table}{col}": continue
                
                res = db.execute(text(f"SELECT DISTINCT {col} FROM {table} LIMIT 20")).fetchall()
                values = [str(row[0]) for row in res if row[0] is not None]
                context += f"- In table '{table}', column '{col}' contains these actual values: {values}\n"
            return context
        except Exception as e:
            return f"Discovery skipped: {str(e)}"

    def generate_sql(self, query: str, discovery_context: str = "") -> str:
        prompt = SQL_GENERATION_PROMPT.replace("{query}", query).replace("{discovery_context}", discovery_context)
        response = llm.invoke(prompt).content
        
        # 1. Clean markdown and tokens
        sql = response.replace("```sql", "").replace("```", "").replace("<|eot_id|>", "").strip()
        
        # 2. Extract strictly from SELECT to the first semicolon
        if "SELECT" in sql.upper():
            start_idx = sql.upper().find("SELECT")
            sql = sql[start_idx:]
            if ";" in sql:
                sql = sql[:sql.find(";") + 1]
            
        return sql

    def run_query(self, query: str) -> dict:
        intent = self.classify_intent(query)
        tool_used = "SQL" if "SQL" in intent else "RAG"
        
        data = []
        db = SessionLocal()
        
        try:
            if tool_used == "SQL":
                discovery_context = self.discover_values(query, db)
                sql = self.generate_sql(query, discovery_context)
                results = db.execute(text(sql)).fetchall()
                data = [dict(row._mapping) for row in results]
                final_answer = "" # Table mode in UI
            else:
                discovery_context = "RAG search - no SQL discovery"
                # Semantic Search
                data = get_clinical_notes_semantic(db, query)
                
                # 2. Synthesize Answer (Only for RAG/Conversational)
                synth_prompt = SYNTHESIS_PROMPT.format(query=query, data=data)
                final_answer = llm.invoke(synth_prompt).content.replace("<|eot_id|>", "")

            # 3. Audit Log
            if tool_used == "SQL":
                log_query = f"--- DISCOVERY ---\n{discovery_context}\n\n--- SQL ---\n{sql}"
            else:
                log_query = query

            log = AuditLog(
                user_query=query,
                tool_used=tool_used,
                tool_query=log_query,
                status="Success",
                result_summary=final_answer[:500] if final_answer else "Table Data Generated"
            )
            db.add(log)
            db.commit()
            
            return {
                "final_answer": final_answer,
                "next_step": tool_used,
                "data_results": data
            }
            
        except Exception as e:
            return {"final_answer": f"Error: {str(e)}", "next_step": "Error", "data_results": []}
        finally:
            db.close()

# Export a simple interface that mimics the old one
class CompatibilityAgent:
    def invoke(self, state: dict):
        agent = ClinicalAgent()
        return agent.run_query(state["query"])

clinical_agent = CompatibilityAgent()

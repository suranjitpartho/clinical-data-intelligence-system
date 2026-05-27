import json
import re
import random
import logging
from sqlalchemy import text
from langgraph.types import interrupt
from app.db.base import SessionLocal
from app.agent.state import AgentState
from app.agent.prompts import CLARIFICATION_PROMPT, CLINICAL_SCHEMA_SUMMARY

logger = logging.getLogger(__name__)

_DISCOVERY_TABLES = {
    "departments": ["name"],
    "staff": ["role"],
    "patients": ["gender"],
    "appointments": ["status"],
    "billing": ["status"],
}


def _get_categorical_values() -> str:
    lines = []
    session = SessionLocal()
    try:
        for table, columns in _DISCOVERY_TABLES.items():
            for col in columns:
                try:
                    rows = session.execute(
                        text(f"SELECT DISTINCT {col} FROM {table} ORDER BY {col}")
                    ).fetchall()
                    vals = [str(r[0]) for r in rows if r[0] is not None]
                    if vals:
                        sample = random.sample(vals, min(3, len(vals)))
                        lines.append(f"- {table}.{col}: (e.g. {', '.join(sample)})")
                except Exception:
                    continue
    finally:
        session.close()
    return "\n".join(lines)


_SPECIFIC_PATTERNS = re.compile(
    r'\b(cardiology|oncology|emergency|pediatrics|orthopedics|'
    r'radiology|neurology|dermatology|endocrinology|'
    r'male|female|last month|last year|this month|'
    r'this year|yesterday|today|dr\.|doctor)\b', re.I
)


def _is_specific_query(query: str) -> bool:
    q = query.lower()
    if _SPECIFIC_PATTERNS.search(q):
        return True
    if any(c.isdigit() for c in q):
        return True
    return False


async def clarify_generate_node(state: AgentState, config, llm):
    thread_id = config.get("configurable", {}).get("thread_id", "unknown")

    if _is_specific_query(state["query"]):
        logger.info(f"[{thread_id}] clarify_generate: query is specific, skipping")
        return {"logs": "\n• No clarification needed."}

    try:
        categorical_values = _get_categorical_values()
        prompt = CLARIFICATION_PROMPT.format(
            query=state["query"],
            clinical_schema=CLINICAL_SCHEMA_SUMMARY,
            categorical_values=categorical_values,
        )
        response = (await llm.ainvoke(prompt, config)).content.strip()
        logger.info(f"[{thread_id}] clarify_generate: LLM response ({len(response)} chars)")
    except Exception as e:
        logger.error(f"[{thread_id}] clarify_generate: LLM failed: {e}", exc_info=True)
        return {"logs": "\n• Clarification generation failed. Proceeding without clarification."}

    try:
        json_str = response.replace("```json", "").replace("```", "").strip()
        questions = json.loads(json_str)
        if not isinstance(questions, list):
            questions = []
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"[{thread_id}] clarify_generate: JSON parse failed: {e}")
        questions = []

    if not questions:
        logger.info(f"[{thread_id}] clarify_generate: no questions needed")
        return {"logs": "\n• No clarification needed."}

    logger.info(f"[{thread_id}] clarify_generate: returning {len(questions)} questions")
    return {"clarification_questions": questions}


async def clarify_resume_node(state: AgentState, config, llm):
    thread_id = config.get("configurable", {}).get("thread_id", "unknown")
    questions = state.get("clarification_questions")

    if not questions:
        logger.info(f"[{thread_id}] clarify_resume: no questions to ask, skipping")
        return {}

    logger.info(f"[{thread_id}] clarify_resume: interrupting with {len(questions)} questions")
    answers = interrupt({"type": "clarify", "questions": questions})
    logger.info(f"[{thread_id}] clarify_resume: resumed with {len(answers) if answers else 0} answers")

    enriched = _enrich_query(state["query"], answers, questions)
    logger.info(f"[{thread_id}] clarify_resume: enriched query ({len(enriched)} chars)")

    return {
        "query": enriched,
        "clarification_answers": answers,
        "logs": "\n• Clarification asked and answered.",
    }


_PARAM_PHRASES = {
    "department_name": lambda v: f" in {v} department",
    "time_period": lambda v: f" for {v}",
    "risk_score_min": lambda v: f" with minimum risk score {v}",
    "metric": lambda v: f" by {v}",
}


def _enrich_query(original_query: str, answers: list, questions: list) -> str:
    if not answers:
        return original_query
    parts = []
    q_map = {q["id"]: q for q in questions} if questions else {}
    for ans in answers:
        qid = ans.get("id", ans.get("question", ""))
        val = ans.get("answer", ans.get("value", str(ans)))
        if not val or val == "All":
            continue
        param = q_map[qid].get("parameter", "") if qid in q_map else ""
        fmt = _PARAM_PHRASES.get(param, lambda v: f" with {v}")
        parts.append(fmt(val))
    return original_query + "".join(parts) if parts else original_query

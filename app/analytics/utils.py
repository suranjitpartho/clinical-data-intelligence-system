import json


def clean_clinical_data(data):
    """Extracts human-readable text from complex JSON/LangGraph structures."""
    if not data:
        return ""
    try:
        val = json.loads(data) if isinstance(data, str) and (data.startswith("{") or data.startswith("[")) else data
        if isinstance(val, dict):
            for key in ["final_answer", "query", "question", "answer", "output", "input", "text"]:
                if key in val and val[key]:
                    return str(val[key])
            return str(val)[:500]
        elif isinstance(val, list) and len(val) > 0:
            last = val[-1]
            if isinstance(last, dict):
                return last.get("content", str(last))
            return str(last)
        return str(val)
    except Exception:
        return str(data)[:500]


def normalize_model_name(raw_model: str) -> str:
    """Normalizes various provider-specific model strings into a single canonical base model name."""
    if not raw_model or raw_model == "N/A":
        return "N/A"
    m_lower = raw_model.lower()
    if "llama-3.3-70b" in m_lower:
        return "Llama-3.3-70B"
    if "gpt-4o" in m_lower:
        return "GPT-4o"
    if "nemotron" in m_lower:
        return "Nemotron-3-120B"
    if "qwen3" in m_lower or "qwen-3" in m_lower:
        return "Qwen-3-Coder"
    if "gpt-oss" in m_lower:
        return "GPT-OSS-120B"
    if "compound" in m_lower:
        return "Groq-Compound"
    return raw_model.upper()

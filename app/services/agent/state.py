import typing
from typing import Annotated, List, Dict, Optional
from typing_extensions import TypedDict

# Python 3.9 + Pydantic 2 Compatibility Patch
if not hasattr(typing, "_TypedDictMeta"):
    typing.TypedDict = TypedDict

class AgentState(TypedDict):
    query: str
    messages: List[Dict] # Conversation history
    tools_needed: List[str]
    tool_query: Optional[str]
    data_results: List[Dict]
    medical_context: List[str] # For RAG snippets
    final_answer: Optional[str]
    error_count: int
    logs: str
    db_session: any

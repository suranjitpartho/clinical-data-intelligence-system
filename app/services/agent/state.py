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
    data_metadata: Dict      # Structured metadata from the SQL tool (total_count, columns, error)
    medical_context: List[str] # For RAG snippets
    reference_context: Dict    # Dictionary of table-specific context (e.g. lab ranges)
    final_answer: Optional[str]
    error_count: int
    logs: str

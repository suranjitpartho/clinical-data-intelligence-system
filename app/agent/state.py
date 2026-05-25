import operator
from typing import Annotated, List, Dict, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    query: Annotated[str, lambda x, y: y]
    messages: Annotated[list, add_messages]
    tools_needed: Annotated[List[str], lambda x, y: y]
    tool_query: Annotated[Optional[str], lambda x, y: y]
    data_results: Annotated[List[Dict], lambda x, y: y]
    data_metadata: Annotated[Dict, lambda x, y: y]
    medical_context: Annotated[List[str], lambda x, y: y]
    reference_context: Annotated[Dict, lambda x, y: y]
    final_answer: Annotated[Optional[str], lambda x, y: y]
    error_count: Annotated[int, lambda x, y: y]
    error: Annotated[Optional[Dict], lambda x, y: y]
    logs: Annotated[str, operator.add]
    cache_hit: Annotated[Optional[bool], lambda x, y: y]

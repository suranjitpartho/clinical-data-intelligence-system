import inspect
from langgraph.graph import StateGraph, START, END
from app.agent.checkpointer import get_checkpointer
from app.agent.state import AgentState
from app.agent.provider import get_llm
from app.agent.nodes.rewrite import rewrite_node
from app.agent.nodes.classify import classify_node
from app.agent.nodes.sql import sql_node
from app.agent.nodes.rag import rag_node
from app.agent.nodes.refine import refine_node
from app.agent.nodes.answer import synthesis_node
from app.agent.nodes.cache import cache_node
from app.agent.nodes.clarify import clarify_generate_node, clarify_resume_node


def _bind_llm(fn, llm):
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
        err = state.get("error")
        if err and err.get("recoverable") and state.get("error_count", 0) < 2:
            return "retry"
        if "rag" in state.get("tools_needed", []) and state.get("data_results"):
            return "rag"
        return "refine"

    def _create_workflow(self):
        graph = StateGraph(AgentState)

        graph.add_node("rewrite", _bind_llm(rewrite_node, self.llm))
        graph.add_node("cache_check", cache_node)
        graph.add_node("clarify_generate", _bind_llm(clarify_generate_node, self.llm))
        graph.add_node("clarify_resume", _bind_llm(clarify_resume_node, self.llm))
        graph.add_node("classify", _bind_llm(classify_node, self.llm))
        graph.add_node("sql_tool", _bind_llm(sql_node, self.llm))
        graph.add_node("rag_tool", rag_node)
        graph.add_node("refine", refine_node)
        graph.add_node("synthesis", _bind_llm(synthesis_node, self.llm))

        graph.add_edge(START, "rewrite")
        graph.add_edge("rewrite", "cache_check")

        graph.add_conditional_edges(
            "cache_check",
            self.route_from_cache,
            {"synthesis": "synthesis", "classify": "clarify_generate"},
        )

        graph.add_conditional_edges(
            "classify",
            self.route_from_classify,
            {"sql": "sql_tool", "rag": "rag_tool", "synthesis": "synthesis"},
        )

        graph.add_conditional_edges(
            "sql_tool",
            self.route_from_sql,
            {"retry": "sql_tool", "rag": "rag_tool", "refine": "refine"},
        )

        graph.add_edge("clarify_generate", "clarify_resume")
        graph.add_edge("clarify_resume", "classify")
        graph.add_edge("rag_tool", "refine")
        graph.add_edge("refine", "synthesis")
        graph.add_edge("synthesis", END)

        return graph.compile(checkpointer=self.memory)

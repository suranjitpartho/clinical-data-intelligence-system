import os
import asyncio
import datetime
from typing import List, Dict, AsyncGenerator
from sqlalchemy import text
from langchain_core.messages import HumanMessage, AIMessage
from app.db.base import SessionLocal
from app.models.logs import AuditLog
from app.agent.graph import ClinicalGraph


NODE_NAMES = {"rewrite", "cache_check", "classify", "sql_tool", "rag_tool", "refine", "synthesis"}


# Setup Langfuse for tracking AI calls
def _init_callbacks() -> list:
    callbacks = []
    if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
        try:
            from langfuse.langchain import CallbackHandler
            callbacks.append(CallbackHandler())
        except Exception as e:
            print(f"Warning: Failed to initialize Langfuse callback: {e}")
    return callbacks


# Check if this is a new or existing conversation, prepare the graph input
async def _resolve_thread(db, thread_id: str, query: str, history: list, memory, model_name: str):
    config = {
        "configurable": {"thread_id": thread_id},
        "metadata": {
            "source": os.getenv("ENV", "development"),
            "agent": "clinical-intelligence",
            "model": model_name,
            "langfuse_session_id": thread_id,
            "langfuse_tags": ["clinical-intelligence", model_name],
        },
    }

    existing = db.execute(
        text("SELECT 1 FROM checkpoints WHERE thread_id = :tid LIMIT 1"),
        {"tid": thread_id},
    ).fetchone()

    if existing:
        meta = db.execute(
            text("SELECT metadata FROM checkpoints WHERE thread_id = :tid ORDER BY checkpoint_id DESC LIMIT 1"),
            {"tid": thread_id},
        ).scalar()
        if meta:
            config["metadata"]["thread_title"] = meta.get("thread_title", "Untitled")
            config["metadata"]["created_at"] = meta.get("created_at")

        input_state = {"query": query, "messages": [HumanMessage(content=query)]}
    else:
        config["metadata"]["thread_title"] = (
            history[0]["content"][:80] if history else query[:80]
        )
        config["metadata"]["created_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

        message_history = []
        if history:
            for m in history:
                if m["role"] == "user":
                    message_history.append(HumanMessage(content=m["content"]))
                elif m["role"] == "assistant":
                    message_history.append(AIMessage(content=m["content"]))

        input_state = {
            "query": query,
            "messages": message_history + [HumanMessage(content=query)],
            "tools_needed": [],
            "tool_query": None,
            "data_results": [],
            "data_metadata": {},
            "medical_context": [],
            "final_answer": None,
            "error_count": 0,
            "logs": "",
            "cache_hit": None,
        }

    prev_logs_len = 0
    if existing:
        loop = asyncio.get_event_loop()
        cp = await loop.run_in_executor(
            None,
            memory.get_tuple,
            {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}},
        )
        if cp:
            prev_logs_len = len(cp.checkpoint.get("channel_values", {}).get("logs", "") or "")

    return config, input_state, prev_logs_len


# Format final output for the frontend
def _build_response(state, prev_logs_len: int) -> dict:
    all_logs = state.get("logs", "") or ""
    run_logs = all_logs[prev_logs_len:] if prev_logs_len else all_logs

    new_messages = []
    for m in state.get("messages", []):
        role = "user" if isinstance(m, HumanMessage) else "assistant"
        new_messages.append({"role": role, "content": m.content})

    return {
        "final_answer": state.get("final_answer", ""),
        "next_step": ", ".join(state.get("tools_needed", [])),
        "data_results": state.get("data_results", []),
        "medical_context": state.get("medical_context", []),
        "tool_query": state.get("tool_query") or "",
        "logs": run_logs,
        "history": new_messages,
        "is_error": False,
    }


# Save audit log and report errors to Langfuse
async def _finalize(db, query: str, state, callbacks: list):
    tool_query = state.get("tool_query")
    status = "Success"
    if (tool_query and "ERROR" in tool_query) or state.get("is_error"):
        status = "Error"

    if status == "Error" and callbacks:
        try:
            trace_id = callbacks[0].get_trace_id()
            if trace_id:
                callbacks[0].langfuse.trace(
                    id=trace_id,
                    level="ERROR",
                    status_message=tool_query or "Query execution failed.",
                )
        except Exception as le:
            print(f"Warning: Failed to update Langfuse trace level: {le}")

    log = AuditLog(
        user_query=query,
        tool_used=", ".join(state.get("tools_needed", [])),
        tool_query=tool_query,
        status=status,
        result_summary=(state.get("final_answer") or "Complete")[:500],
    )
    db.add(log)
    db.commit()

    if callbacks:
        try:
            callbacks[0].flush()
        except Exception:
            pass


# Handle rate limits and other failures gracefully
def _error_response(e):
    import traceback
    error_msg = str(e)
    print(f"[{type(e).__name__}]: {error_msg}")
    traceback.print_exc()
    if "429" in error_msg or "rate limit" in error_msg.lower():
        return (
            "**Model Rate Limit Reached**: The current AI model has reached its daily or minute-level token limit. "
            "To continue your analysis without interruption, please switch to a different model or provider "
            "using the selection menu at the bottom of the left sidebar."
        ), f"Technical Details: {error_msg}", True
    return f"Graph Error ({type(e).__name__}): {error_msg}", "", True


# Run a query through the AI graph and return the full answer
async def arun_query(
    query: str,
    thread_id: str = "default",
    history: List[Dict] = None,
    provider: str = None,
    model_name: str = None,
) -> Dict:
    graph = ClinicalGraph(provider=provider, model_name=model_name)
    db = SessionLocal()
    try:
        callbacks = _init_callbacks()
        config, input_state, prev_logs_len = await _resolve_thread(
            db, thread_id, query, history, graph.memory, graph.model_name,
        )
        config["callbacks"] = callbacks

        final_state = await graph.workflow.ainvoke(input_state, config=config)
        await _finalize(db, query, final_state, callbacks)
        return _build_response(final_state, prev_logs_len)
    except Exception as e:
        final_answer, logs, is_error = _error_response(e)
        return {"final_answer": final_answer, "data_results": [], "logs": logs, "is_error": is_error}
    finally:
        db.close()


# Run a query and stream back events (nodes, tokens, final answer) in real-time
async def arun_query_stream(
    query: str,
    thread_id: str = "default",
    history: List[Dict] = None,
    provider: str = None,
    model_name: str = None,
) -> AsyncGenerator[Dict, None]:
    graph = ClinicalGraph(provider=provider, model_name=model_name)
    db = SessionLocal()
    try:
        callbacks = _init_callbacks()
        config, input_state, prev_logs_len = await _resolve_thread(
            db, thread_id, query, history, graph.memory, graph.model_name,
        )
        config["callbacks"] = callbacks

        current_node = None
        async for event in graph.workflow.astream_events(input_state, config, version="v2"):
            event_type = event["event"]
            name = event.get("name", "")

            if event_type == "on_chain_start" and name in NODE_NAMES:
                current_node = name
                yield {"type": "node_start", "node": name}
            elif event_type == "on_chain_end" and name in NODE_NAMES:
                yield {"type": "node_end", "node": name}
                current_node = None
            elif event_type == "on_chat_model_stream" and current_node == "synthesis":
                chunk = event["data"]["chunk"]
                token_text = chunk.get("content", "") if isinstance(chunk, dict) else getattr(chunk, "content", "")
                if token_text:
                    yield {"type": "token", "content": token_text}

        loop = asyncio.get_event_loop()
        cp = await loop.run_in_executor(
            None,
            graph.memory.get_tuple,
            {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}},
        )
        final_state = cp.checkpoint.get("channel_values", {}) if cp else None

        if not final_state:
            yield {"type": "error", "message": "Failed to retrieve final graph state"}
            return

        await _finalize(db, query, final_state, callbacks)
        yield {"type": "done", **_build_response(final_state, prev_logs_len)}
    except Exception as e:
        final_answer, logs, _ = _error_response(e)
        yield {"type": "error", "message": final_answer, "logs": logs}
    finally:
        db.close()

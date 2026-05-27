import os
import uuid
import asyncio
import datetime
import logging
from typing import List, Dict, AsyncGenerator
from sqlalchemy import text
from langchain_core.messages import HumanMessage, AIMessage
from app.db.base import SessionLocal
from app.models.logs import AuditLog
from langgraph.types import Command
from app.agent.graph import ClinicalGraph
from app.agent.exceptions import ClinicalError, RateLimitError

logging.basicConfig(
    filename=os.path.join(os.path.dirname(os.path.dirname(__file__)), "app.log"),
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    force=True,
)
logger = logging.getLogger(__name__)


NODE_NAMES = {"rewrite", "cache_check", "clarify_generate", "clarify_resume", "classify", "sql_tool", "rag_tool", "refine", "synthesis"}


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

    logger.info(f"Resolving thread {thread_id} (existing={db.execute(text('SELECT 1 FROM checkpoints WHERE thread_id = :tid LIMIT 1'), {'tid': thread_id}).fetchone() is not None})")

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
        title = history[0]["content"][:80] if history else query[:80]
        config["metadata"]["thread_title"] = title
        config["metadata"]["langfuse_trace_name"] = title
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
            "error": None,
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

    state_error = state.get("error")
    return {
        "final_answer": state.get("final_answer", ""),
        "next_step": ", ".join(state.get("tools_needed", [])),
        "data_results": state.get("data_results", []),
        "medical_context": state.get("medical_context", []),
        "tool_query": state.get("tool_query") or "",
        "logs": run_logs,
        "history": new_messages,
        "is_error": state_error is not None,
        "error_code": state_error.get("code") if state_error else None,
    }


# Save audit log and report errors to Langfuse
async def _finalize(db, query: str, state, callbacks: list):
    tool_query = state.get("tool_query") or "Query execution failed."
    status = "Error" if state.get("error") else "Success"

    if status == "Error" and callbacks:
        try:
            error_trace_id = callbacks[0].last_trace_id
            if error_trace_id:
                callbacks[0].langfuse.trace(
                    id=error_trace_id,
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

    if isinstance(e, RateLimitError):
        return (
            "**Model Rate Limit Reached**: The current AI model has reached its daily or minute-level token limit. "
            "To continue your analysis without interruption, please switch to a different model or provider "
            "using the selection menu at the bottom of the left sidebar."
        ), f"Technical Details: {error_msg}", True, e.code if isinstance(e, ClinicalError) else "RATE_LIMIT"

    code = e.code if isinstance(e, ClinicalError) else "UNKNOWN_ERROR"
    return f"Graph Error ({type(e).__name__}): {error_msg}", "", True, code


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
        config, input_state, prev_logs_len = await _resolve_thread(
            db, thread_id, query, history, graph.memory, graph.model_name,
        )
        callbacks = _init_callbacks()
        config["callbacks"] = callbacks

        final_state = await graph.workflow.ainvoke(input_state, config=config)
        await _finalize(db, query, final_state, callbacks)
        return _build_response(final_state, prev_logs_len)
    except Exception as e:
        final_answer, logs, is_error, error_code = _error_response(e)
        return {"final_answer": final_answer, "data_results": [], "logs": logs, "is_error": is_error, "error_code": error_code}
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
        config, input_state, prev_logs_len = await _resolve_thread(
            db, thread_id, query, history, graph.memory, graph.model_name,
        )
        callbacks = _init_callbacks()
        config["callbacks"] = callbacks

        request_id = uuid.uuid4().hex
        config["metadata"]["langfuse_metadata"] = {"request_id": request_id}

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

        # Check if graph was interrupted by clarify node
        logger.info(f"Stream ended for {thread_id}, checking for interrupts")
        snapshot = await graph.workflow.aget_state(
            {"configurable": {"thread_id": thread_id}}
        )
        if snapshot and snapshot.tasks:
            for task in snapshot.tasks:
                if hasattr(task, 'interrupts') and task.interrupts:
                    questions = task.interrupts[0].value.get("questions", [])
                    logger.info(f"Interrupt found for {thread_id}: {len(questions)} questions")
                    yield {"type": "clarify", "questions": questions, "request_id": request_id}
                    if callbacks:
                        try:
                            tid = callbacks[0].last_trace_id
                            if tid:
                                callbacks[0].langfuse.trace(id=tid, input=query)
                                callbacks[0].flush()
                        except Exception:
                            pass
                    return
        logger.info(f"No interrupt found for {thread_id}, normal completion")

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

        if callbacks:
            try:
                tid = callbacks[0].last_trace_id
                if tid:
                    callbacks[0].langfuse.trace(id=tid, input=query)
            except Exception:
                pass

        await _finalize(db, query, final_state, callbacks)
        yield {"type": "done", **_build_response(final_state, prev_logs_len)}
    except Exception as e:
        final_answer, logs, _, error_code = _error_response(e)
        yield {"type": "error", "message": final_answer, "logs": logs, "code": error_code}
    finally:
        db.close()


async def arun_resume_stream(
    thread_id: str,
    answers: list,
    provider: str = None,
    model_name: str = None,
    request_id: str = None,
) -> AsyncGenerator[Dict, None]:
    graph = ClinicalGraph(provider=provider, model_name=model_name)
    loop = asyncio.get_event_loop()
    cp = await loop.run_in_executor(
        None,
        graph.memory.get_tuple,
        {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}},
    )
    existing_meta = cp.metadata or {} if cp else {}
    callbacks = _init_callbacks()
    config = {
        "configurable": {"thread_id": thread_id},
        "metadata": {
            "source": os.getenv("ENV", "development"),
            "agent": "clinical-intelligence",
            "model": model_name,
            "langfuse_session_id": thread_id,
            "langfuse_tags": ["clinical-intelligence", model_name],
            "thread_title": existing_meta.get("thread_title", "Untitled"),
            "created_at": existing_meta.get("created_at"),
            "langfuse_trace_name": f"Clarify Resume — {existing_meta.get('thread_title', 'Untitled')}",
            "langfuse_metadata": {"request_id": request_id} if request_id else {},
        },
        "callbacks": callbacks,
    }
    logger.info(f"Resuming thread {thread_id} with {len(answers)} answers")
    try:
        final_state = await graph.workflow.ainvoke(
            Command(resume=answers), config,
        )
        logger.info(f"Resume completed for thread {thread_id}")

        enriched_query = final_state.get("query", "")
        if callbacks and enriched_query:
            try:
                tid = callbacks[0].last_trace_id
                if tid:
                    callbacks[0].langfuse.trace(id=tid, input=enriched_query)
            except Exception:
                pass

        answer = final_state.get("final_answer", "")
        if answer:
            yield {"type": "token", "content": answer}

        if callbacks:
            try:
                callbacks[0]._langfuse_client.flush()
            except Exception:
                pass

        yield {"type": "done", **_build_response(final_state, 0)}
    except Exception as e:
        logger.error(f"Resume failed for thread {thread_id}: {e}", exc_info=True)
        final_answer, logs, _, error_code = _error_response(e)
        yield {"type": "error", "message": final_answer, "logs": logs, "code": error_code}

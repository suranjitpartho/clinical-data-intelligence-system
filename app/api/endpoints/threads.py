import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from app.db.base import SessionLocal
from app.agent.checkpointer import get_checkpointer
from app.agent.exceptions import ThreadNotFoundError
from app.agent.graph import ClinicalGraph
from app.agent.service import arun_resume_stream
from app.schemas.query import ResumeRequest, _format_sse
from app.auth.deps import get_current_user

router = APIRouter(tags=["threads"], dependencies=[Depends(get_current_user)])


# List all past conversations for the sidebar
@router.get("/threads")
async def list_threads(page: int = 1, page_size: int = 25):
    get_checkpointer()
    db = SessionLocal()
    try:
        total = db.execute(text("""
            SELECT COUNT(*) FROM (
                SELECT DISTINCT ON (thread_id) 1 FROM checkpoints
            ) sub
        """)).scalar() or 0

        offset = (page - 1) * page_size
        rows = db.execute(text("""
            SELECT thread_id, metadata FROM (
                SELECT DISTINCT ON (thread_id) thread_id, metadata
                FROM checkpoints
                ORDER BY thread_id, checkpoint_id DESC
            ) sub
            ORDER BY (sub.metadata->>'created_at') DESC NULLS LAST
            LIMIT :limit OFFSET :offset
        """), {"limit": page_size, "offset": offset}).fetchall()

        result = []
        for row in rows:
            meta = row.metadata or {}
            result.append({
                "thread_id": row.thread_id,
                "title": meta.get("thread_title", "Untitled"),
                "created_at": meta.get("created_at"),
            })

        return {
            "threads": result,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": offset + page_size < total,
        }
    except Exception as e:
        print(f"Error listing threads: {e}")
        return {"threads": [], "total": 0, "page": 1, "page_size": page_size, "has_more": False}
    finally:
        db.close()


# Load a single conversation with all its messages
@router.get("/threads/{thread_id}")
async def get_thread(thread_id: str):
    checkpointer = get_checkpointer()
    config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}
    loop = asyncio.get_event_loop()
    checkpoint_tuple = await loop.run_in_executor(None, checkpointer.get_tuple, config)
    if not checkpoint_tuple:
        raise ThreadNotFoundError(details={"thread_id": thread_id})
    messages = []
    for msg in checkpoint_tuple.checkpoint.get("channel_values", {}).get("messages", []):
        role = "user" if getattr(msg, "type", "") == "human" else "assistant"
        entry = {"role": role, "content": str(msg.content)}
        if role == "assistant":
            akw = getattr(msg, "additional_kwargs", {}) or {}
            if akw.get("data_results"):
                entry["data_results"] = akw["data_results"]
            if akw.get("tool_query"):
                entry["tool_query"] = akw["tool_query"]
            if akw.get("next_step"):
                entry["next_step"] = akw["next_step"]
        messages.append(entry)
    meta = checkpoint_tuple.metadata or {}
    return {
        "thread_id": thread_id,
        "messages": messages,
        "title": meta.get("thread_title", "Untitled"),
        "created_at": meta.get("created_at"),
    }


# Resume a paused thread with clarification answers
@router.post("/threads/{thread_id}/resume")
async def resume_thread(thread_id: str, request: ResumeRequest):
    try:
        events = arun_resume_stream(
            thread_id=thread_id,
            answers=request.answers,
            provider=request.provider,
            model_name=request.model,
            request_id=request.request_id,
        )
        return StreamingResponse(
            _format_sse(events),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get current graph state (includes pending interrupts)
@router.get("/threads/{thread_id}/state")
async def get_thread_state(thread_id: str):
    graph = ClinicalGraph()
    try:
        snapshot = await graph.workflow.aget_state(
            {"configurable": {"thread_id": thread_id}}
        )
        if not snapshot:
            raise ThreadNotFoundError(details={"thread_id": thread_id})
        interrupt_data = None
        if snapshot.tasks:
            for task in snapshot.tasks:
                if hasattr(task, 'interrupts') and task.interrupts:
                    interrupt_data = task.interrupts[0].value
                    break
        values = snapshot.values or {}
        return {
            "thread_id": thread_id,
            "interrupted": interrupt_data is not None,
            "clarification_questions": interrupt_data.get("questions", []) if interrupt_data else [],
            "next_node": snapshot.next[0] if snapshot.next else None,
            "messages": [
                {"role": "user" if getattr(m, "type", "") == "human" else "assistant", "content": m.content}
                for m in values.get("messages", [])
            ],
        }
    except ThreadNotFoundError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

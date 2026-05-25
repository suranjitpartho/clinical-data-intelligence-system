import asyncio
from fastapi import APIRouter
from sqlalchemy import text
from app.db.base import SessionLocal
from app.agent.checkpointer import get_checkpointer
from app.agent.exceptions import ThreadNotFoundError

router = APIRouter(tags=["threads"])


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

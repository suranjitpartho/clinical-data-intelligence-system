from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.schemas.query import QueryRequest, _format_sse
from app.agent.service import arun_query, arun_query_stream

router = APIRouter(tags=["query"])


# Send a question and get the full response
@router.post("/query")
async def process_query(request: QueryRequest):
    try:
        result = await arun_query(
            query=request.query,
            thread_id=request.thread_id,
            history=request.history,
            provider=request.provider,
            model_name=request.model,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Send a question and stream back the response token-by-token
@router.post("/query/stream")
async def process_query_stream(request: QueryRequest):
    events = arun_query_stream(
        query=request.query,
        thread_id=request.thread_id,
        history=request.history,
        provider=request.provider,
        model_name=request.model,
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

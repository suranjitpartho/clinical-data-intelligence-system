import json
import datetime
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str
    model: str = None
    provider: str = None
    thread_id: str = "default_session"
    history: list = []


class ExportRequest(BaseModel):
    sql: str


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: dict | None = None


class _SafeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)


async def _format_sse(events):
    async for event in events:
        event_type = event.pop("type", "")
        data = json.dumps(event, cls=_SafeEncoder)
        yield f"event: {event_type}\ndata: {data}\n\n"

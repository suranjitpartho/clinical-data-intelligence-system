import os
import json
from fastapi import APIRouter

router = APIRouter(prefix="/embedding", tags=["embedding"])

STATUS_FILE = "/tmp/embedding_status.json"


@router.get("/status")
async def get_embedding_status():
    default = {"status": "unknown", "done": 0, "total": 0}
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return default

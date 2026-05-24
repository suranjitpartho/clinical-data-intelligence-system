import os
import json
from fastapi import APIRouter

router = APIRouter(tags=["config"])


# List available AI models from models.json
@router.get("/models")
async def get_models():
    try:
        path = os.path.join(os.path.dirname(__file__), "..", "..", "services", "models.json")
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return []


# Return the currently active model and provider
@router.get("/config")
async def get_config():
    return {
        "model_name": os.getenv("AI_MODEL", "Unknown"),
        "provider": os.getenv("AI_PROVIDER", "groq"),
    }

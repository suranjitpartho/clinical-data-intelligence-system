import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.services.agent import clinical_agent
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

app = FastAPI(title="CDIS AI API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str
    model: str = None
    provider: str = None
    thread_id: str = "default_session"
    history: list = []

@app.get("/models")
async def get_models():
    try:
        path = os.path.join(os.path.dirname(__file__), "services", "models.json")
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        return []

@app.get("/config")
async def get_config():
    return {
        "model_name": os.getenv("AI_MODEL", "Unknown"),
        "provider": os.getenv("AI_PROVIDER", "groq")
    }

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.services.analytics import analytics_service

@app.get("/analytics")
async def get_analytics():
    return analytics_service.get_system_metrics()

@app.post("/query")
async def process_query(request: QueryRequest):
    try:
        # Pass to our dynamic Clinical Agent
        result = clinical_agent.invoke({
            "query": request.query,
            "model": request.model,
            "provider": request.provider,
            "thread_id": request.thread_id,
            "history": request.history
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- UI Serving Logic ---
# Mount the static files (React build) if the directory exists
static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(static_path, "assets")), name="static_assets")

@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    # If the path matches an API route, FastAPI already handled it.
    # Otherwise, we serve the React index.html
    if os.path.exists(os.path.join(static_path, "index.html")):
        return FileResponse(os.path.join(static_path, "index.html"))
    return {"message": "API is running, but UI files were not found. Build the frontend first."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

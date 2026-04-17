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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

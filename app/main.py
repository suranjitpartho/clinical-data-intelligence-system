import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.services.agent import clinical_agent
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env
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

@app.get("/config")
async def get_config():
    return {"model_name": os.getenv("AI_MODEL", "Unknown")}

@app.post("/query")
async def process_query(request: QueryRequest):
    try:
        # Pass to our stabilized Clinical Agent
        result = clinical_agent.invoke({"query": request.query})
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

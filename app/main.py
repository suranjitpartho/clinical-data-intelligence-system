from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Clinical Data Intelligence System API",
    description="AI-powered clinical intelligence for a private medical clinic",
    version="0.1.0"
)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.services.agent import clinical_agent
from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str

@app.get("/")
async def root():
    return {"message": "Welcome to Clinical Data Intelligence System API", "docs": "/docs"}

@app.post("/ai/query")
async def ask_agent(request: QueryRequest):
    """
    Orchestrates the query through the LangGraph agent.
    """
    initial_state = {
        "query": request.query,
        "messages": [],
        "next_step": "",
        "data_results": [],
        "final_answer": ""
    }
    
    result = clinical_agent.invoke(initial_state)
    
    return {
        "answer": result["final_answer"],
        "logic_path": result["next_step"],
        "data_count": len(result["data_results"])
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

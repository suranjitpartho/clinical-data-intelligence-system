import os
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
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

import csv
import io
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy import text
from app.db.base import SessionLocal

class QueryRequest(BaseModel):
    query: str
    model: str = None
    provider: str = None
    thread_id: str = "default_session"
    history: list = []

class ExportRequest(BaseModel):
    sql: str

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
from app.services.analytics import analytics_service

@app.get("/analytics")
async def get_analytics(days: int = 7, page: int = 1, page_size: int = 10):
    return analytics_service.get_system_metrics(days_back=days, page=page, page_size=page_size)

@app.get("/analytics/operational")
async def get_operational_analytics(days: int = 7, model: str = None):
    return analytics_service.get_operational_analytics(days_back=days, model_filter=model)

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

@app.post("/export-csv")
async def export_csv(request: ExportRequest):
    """
    Scalable CSV export that streams results from the database.
    Prevents memory overflow even with millions of rows.
    """
    if not request.sql or not request.sql.strip().upper().startswith(("SELECT", "WITH")):
        raise HTTPException(status_code=400, detail="Invalid SQL query for export")
    
    def generate_csv():
        db = SessionLocal()
        try:
            # We execute the query and fetch in a way that doesn't load everything into RAM
            # result.yield_per(1000) could be used if it was a query object, 
            # for raw text we iterate the cursor.
            result = db.execute(text(request.sql))
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write Header
            keys = result.keys()
            writer.writerow(keys)
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)
            
            # Write Rows in chunks
            for row in result:
                writer.writerow(row)
                yield output.getvalue()
                output.seek(0)
                output.truncate(0)
        except Exception as e:
            # In a stream, we can't easily change status code once started, 
            # but we can yield the error in the CSV for debugging or log it.
            print(f"Export Error: {e}")
        finally:
            db.close()

    return StreamingResponse(
        generate_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=clinical_intelligence_export.csv"}
    )

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

import os
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.endpoints.query import router as query_router
from app.api.endpoints.threads import router as threads_router
from app.api.endpoints.config import router as config_router
from app.api.endpoints.analytics import router as analytics_router
from app.api.endpoints.export import router as export_router

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.agent.checkpointer import get_checkpointer, close_checkpointer
    get_checkpointer()
    yield
    close_checkpointer()


app = FastAPI(title="CDIS AI API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query_router)
app.include_router(threads_router)
app.include_router(config_router)
app.include_router(analytics_router)
app.include_router(export_router)

static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(static_path, "assets")), name="static_assets")


@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    if os.path.exists(os.path.join(static_path, "index.html")):
        return FileResponse(os.path.join(static_path, "index.html"))
    return {"message": "API is running, but UI files were not found. Build the frontend first."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

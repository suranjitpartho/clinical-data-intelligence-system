import os
from dotenv import load_dotenv

load_dotenv()

os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.endpoints.query import router as query_router
from app.api.endpoints.threads import router as threads_router
from app.api.endpoints.config import router as config_router
from app.api.endpoints.analytics import router as analytics_router
from app.api.endpoints.export import router as export_router
from app.api.endpoints.auth import router as auth_router
from app.agent.exceptions import ClinicalError


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


@app.exception_handler(ClinicalError)
async def clinical_error_handler(request: Request, exc: ClinicalError):
    status_map = {"INVALID_QUERY": 400, "THREAD_NOT_FOUND": 404, "SCHEMA_ERROR": 500}
    return JSONResponse(
        status_code=status_map.get(exc.code, 500),
        content={"code": exc.code, "message": str(exc), "details": exc.details},
    )


app.include_router(query_router)
app.include_router(threads_router)
app.include_router(config_router)
app.include_router(analytics_router)
app.include_router(export_router)
app.include_router(auth_router, prefix="/api")

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

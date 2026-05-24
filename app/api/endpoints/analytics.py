from fastapi import APIRouter, BackgroundTasks
from app.analytics import analytics_service, obs_sync_service

router = APIRouter(tags=["analytics"])


# Get dashboard summary (total queries, errors, token usage)
@router.get("/analytics")
async def get_analytics(days: int = 7, page: int = 1, page_size: int = 10):
    return analytics_service.get_system_metrics(days_back=days, page=page, page_size=page_size)


# Get detailed charts (daily trends, model comparison, heatmap)
@router.get("/analytics/operational")
async def get_operational_analytics(days: int = 7, model: str = None):
    return analytics_service.get_operational_analytics(days_back=days, model_filter=model)


# Pull the latest data from Langfuse into the local database
@router.post("/analytics/sync")
async def sync_analytics(background_tasks: BackgroundTasks, days: int = 30):
    background_tasks.add_task(obs_sync_service.sync_latest, days_back=30)
    return {"status": "accepted", "message": "Synchronization started in background"}

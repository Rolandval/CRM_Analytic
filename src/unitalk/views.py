from fastapi import APIRouter

from src.services.call_sync_service import sync_calls
from src.unitalk.schemas import SyncResponse

unitalk_router = APIRouter(prefix="/unitalk", tags=["Unitalk Sync"])


@unitalk_router.post("/sync/all", response_model=SyncResponse)
async def sync_all_calls():
    """Sync all calls from Unitalk (from configured start date to now)."""
    stats = await sync_calls(today=False)
    return SyncResponse(status="success", message=f"Synced {stats.total} calls", stats=stats)


@unitalk_router.post("/sync/today", response_model=SyncResponse)
async def sync_today_calls():
    """Sync only today's calls from Unitalk."""
    stats = await sync_calls(today=True)
    return SyncResponse(status="success", message=f"Synced {stats.total} calls for today", stats=stats)

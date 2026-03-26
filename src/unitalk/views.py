from fastapi import APIRouter

from src.services.call_sync_service import sync_calls
from src.services.ai_sync_service import sync_analytics, AnalyticsSyncStats
from src.unitalk.schemas import SyncResponse, AnalyticsSyncResponse, AnalyticsSyncStats as AnalyticsSyncStatsSchema

unitalk_router = APIRouter(prefix="/unitalk", tags=["Unitalk Sync"])


# ── API-sync (через Unitalk REST API) ─────────────────────────────────────────

@unitalk_router.post("/sync/all", response_model=SyncResponse)
async def sync_all_calls():
    """Sync all calls from Unitalk API (from configured start date to now)."""
    stats = await sync_calls(today=False)
    return SyncResponse(status="success", message=f"Synced {stats.total} calls", stats=stats)


@unitalk_router.post("/sync/today", response_model=SyncResponse)
async def sync_today_calls():
    """Sync only today's calls from Unitalk API."""
    stats = await sync_calls(today=True)
    return SyncResponse(status="success", message=f"Synced {stats.total} calls for today", stats=stats)


# ── Web-parser analytics (через Selenium) ─────────────────────────────────────

@unitalk_router.post("/analytics/sync/all", response_model=AnalyticsSyncResponse)
async def analytics_sync_all():
    """
    Запускає Selenium-парсер по всіх дзвінках на сайті Unitalk
    та зберігає мовну аналітику (topic, key_points, next_steps) у таблицю CallAiAnalytic.

    ⚠️  Тривала операція — може займати кілька хвилин залежно від кількості дзвінків.
    """
    result: AnalyticsSyncStats = await sync_analytics(today=False)
    stats_schema = AnalyticsSyncStatsSchema(
        total_scraped=result.total_scraped,
        saved=result.saved,
        skipped_no_data=result.skipped_no_data,
        skipped_no_match=result.skipped_no_match,
        errors=result.errors,
    )
    return AnalyticsSyncResponse(
        status="success",
        message=f"Аналітику зібрано: {result.saved} дзвінків збережено з {result.total_scraped} знайдених",
        stats=stats_schema,
    )


@unitalk_router.post("/analytics/sync/today", response_model=AnalyticsSyncResponse)
async def analytics_sync_today():
    """
    Запускає Selenium-парсер тільки по сьогоднішніх дзвінках
    та зберігає мовну аналітику у таблицю CallAiAnalytic.
    """
    result: AnalyticsSyncStats = await sync_analytics(today=True)
    stats_schema = AnalyticsSyncStatsSchema(
        total_scraped=result.total_scraped,
        saved=result.saved,
        skipped_no_data=result.skipped_no_data,
        skipped_no_match=result.skipped_no_match,
        errors=result.errors,
    )
    return AnalyticsSyncResponse(
        status="success",
        message=f"Аналітику зібрано: {result.saved} дзвінків збережено з {result.total_scraped} знайдених",
        stats=stats_schema,
    )

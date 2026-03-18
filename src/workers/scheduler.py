"""
APScheduler setup for background jobs.

Jobs registered here:
1. daily_sync       — sync all Unitalk calls every morning
2. today_sync       — sync today's calls every 30 minutes during business hours
3. ai_process_queue — process pending AI analytics queue every hour

The scheduler is started/stopped via FastAPI's lifespan context.
"""
import asyncio
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def _run_daily_sync() -> None:
    """Sync all calls (full history). Runs once a day."""
    from src.services.call_sync_service import sync_calls
    logger.info("scheduler_job_start", job="daily_sync")
    try:
        stats = await sync_calls(today=False)
        logger.info("scheduler_job_done", job="daily_sync", **stats.model_dump())
    except Exception as exc:
        logger.error("scheduler_job_error", job="daily_sync", error=str(exc))


async def _run_today_sync() -> None:
    """Sync today's calls. Runs every 30 minutes."""
    from src.services.call_sync_service import sync_calls
    logger.info("scheduler_job_start", job="today_sync")
    try:
        stats = await sync_calls(today=True)
        logger.info("scheduler_job_done", job="today_sync", **stats.model_dump())
    except Exception as exc:
        logger.error("scheduler_job_error", job="today_sync", error=str(exc))


async def _run_ai_queue() -> None:
    """Process pending AI analytics. Runs every hour."""
    from src.ai.processor import process_pending_queue
    logger.info("scheduler_job_start", job="ai_queue")
    try:
        processed = await process_pending_queue()
        logger.info("scheduler_job_done", job="ai_queue", processed=processed)
    except Exception as exc:
        logger.error("scheduler_job_error", job="ai_queue", error=str(exc))


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")

    # Daily full sync at configured time (default 6:00 AM UTC)
    scheduler.add_job(
        _run_daily_sync,
        trigger=CronTrigger(
            hour=settings.sync_cron_hour,
            minute=settings.sync_cron_minute,
        ),
        id="daily_sync",
        name="Daily Unitalk full sync",
        replace_existing=True,
        misfire_grace_time=300,
    )

    # Today sync every 30 minutes during business hours (8–20 UTC)
    scheduler.add_job(
        _run_today_sync,
        trigger=CronTrigger(hour="8-20", minute="*/30"),
        id="today_sync",
        name="Today Unitalk sync (every 30 min)",
        replace_existing=True,
        misfire_grace_time=60,
    )

    # AI queue processing every hour
    if settings.ai_processing_enabled:
        scheduler.add_job(
            _run_ai_queue,
            trigger=IntervalTrigger(hours=1),
            id="ai_queue",
            name="AI analytics queue processor",
            replace_existing=True,
            misfire_grace_time=120,
        )

    return scheduler


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = create_scheduler()
    return _scheduler


async def start_scheduler() -> None:
    if not settings.scheduler_enabled:
        logger.info("scheduler_disabled")
        return
    scheduler = get_scheduler()
    scheduler.start()
    logger.info("scheduler_started", jobs=len(scheduler.get_jobs()))


async def stop_scheduler() -> None:
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("scheduler_stopped")

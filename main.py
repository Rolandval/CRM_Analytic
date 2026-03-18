"""
CRM Database API — application entry point.

Startup sequence:
1. Configure structured logging
2. Connect to DB (verify via engine.connect)
3. Start background scheduler
4. Register all routers

Shutdown sequence:
1. Stop scheduler
2. Dispose DB connection pool
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.exceptions import register_exception_handlers
from core.logging import get_logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
    setup_logging()
    logger = get_logger(__name__)
    logger.info("app_startup", env=settings.environment, version=settings.app_version)

    from db.database import engine
    async with engine.connect() as conn:
        await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
    logger.info("db_connected")

    from src.workers.scheduler import start_scheduler
    await start_scheduler()

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    from src.workers.scheduler import stop_scheduler
    await stop_scheduler()

    from db.database import close_db
    await close_db()
    logger.info("app_shutdown")


# ── App factory ───────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-grade CRM API with Unitalk integration and AI analytics",
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# ── Exception handlers ────────────────────────────────────────────────────────
register_exception_handlers(app)

# ── Routers ───────────────────────────────────────────────────────────────────
from src.calls.routes import calls_router
from src.unitalk.views import unitalk_router
from src.users.routes import users_router

app.include_router(calls_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(unitalk_router, prefix="/api/v1")


# ── Health check (unauthenticated) ────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health():
    from db.database import engine
    from sqlalchemy import text
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ok", "version": settings.app_version}


@app.get("/", tags=["System"])
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }

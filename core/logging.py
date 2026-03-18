"""
Structured logging configuration using structlog.

Usage:
    from core.logging import get_logger
    logger = get_logger(__name__)
    logger.info("event", key="value")
"""
import logging
import sys
import structlog
from core.config import settings


def setup_logging() -> None:
    """Configure structlog + stdlib logging to emit structured JSON in production,
    pretty console output in development."""

    log_level = logging.DEBUG if settings.debug else logging.INFO

    # ── stdlib root logger ────────────────────────────────────────────────────
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )
    # Silence noisy third-party loggers
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # ── structlog processors chain ────────────────────────────────────────────
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.environment == "production":
        # JSON renderer — machine-readable for log aggregators (ELK, Loki, etc.)
        renderer = structlog.processors.JSONRenderer()
    else:
        # Human-readable coloured console output
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(log_level)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)

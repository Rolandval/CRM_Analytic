from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────────────────────
    app_name: str = "CRM Database API"
    app_version: str = "2.0.0"
    debug: bool = False
    environment: str = Field(default="development", pattern="^(development|staging|production)$")

    # ── Database ───────────────────────────────────────────────────────────────
    database_url: str
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_echo: bool = False  # Never echo SQL in production

    # ── Auth ───────────────────────────────────────────────────────────────────
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 8  # 8 hours

    # ── CORS ───────────────────────────────────────────────────────────────────
    # Stored as a plain string to avoid pydantic-settings JSON-decode issues.
    # Format: comma-separated origins, e.g. "http://localhost:5173,http://localhost:3000"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"

    def get_cors_origins(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # ── Unitalk API ────────────────────────────────────────────────────────────
    api_token: str
    unitalk_api_url: str = "https://api.unitalk.cloud/api/history/get"
    unitalk_sync_from_date: str = "2025-09-01 00:00:00"
    unitalk_request_timeout: int = 60  # seconds
    unitalk_page_size: int = 1000

    # ── Scheduler ─────────────────────────────────────────────────────────────
    scheduler_enabled: bool = True
    # Cron expression for daily sync (default: every day at 6 AM)
    sync_cron_hour: int = 6
    sync_cron_minute: int = 0

    # ── AI (future) ───────────────────────────────────────────────────────────
    openai_api_key: str = ""
    ai_processing_enabled: bool = False

    # ── Unitalk Web Parser (Selenium) ─────────────────────────────────────────
    # URL кабінету: https://my.unitalk.cloud (захардкоджено у parser)
    unitalk_web_username: str = ""        # Email для входу в my.unitalk.cloud
    unitalk_web_password: str = ""        # Пароль
    unitalk_parser_headless: bool = True  # False — показувати браузер (debug)
    unitalk_parser_page_timeout: int = 30
    unitalk_parser_element_timeout: int = 15
    unitalk_parser_max_days: int = 30     # кількість днів назад для sync_all


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

from typing import Any, List
from pydantic import BaseModel
from src.schemas.call import SyncStats


class SyncResponse(BaseModel):
    status: str
    message: str
    stats: SyncStats


class AnalyticsSyncStats(BaseModel):
    total_scraped: int
    saved: int
    skipped_no_data: int
    skipped_no_match: int
    errors: int


class AnalyticsSyncResponse(BaseModel):
    status: str
    message: str
    stats: AnalyticsSyncStats


class CategorizationStats(BaseModel):
    total: int
    categorized: int
    skipped_no_topics: int
    errors: int
    results: List[Any] = []


class CategorizationResponse(BaseModel):
    status: str
    message: str
    stats: CategorizationStats

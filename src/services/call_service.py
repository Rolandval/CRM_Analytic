"""Call service — business logic for reading / filtering calls."""
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import CallNotFound
from core.logging import get_logger
from db.models import Call
from src.repositories.call_repository import CallRepository
from src.schemas.call import CallFilter

logger = get_logger(__name__)


class CallService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = CallRepository(session)

    async def get_call(self, call_id: int) -> Call:
        call = await self._repo.get_by_id(call_id)
        if not call:
            raise CallNotFound(f"Call {call_id} not found")
        return call

    async def list_calls(
        self,
        filters: CallFilter,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Call], int]:
        offset = (page - 1) * page_size
        return await self._repo.list_with_filters(filters, offset=offset, limit=page_size)

    async def get_stats(self) -> dict:
        return await self._repo.get_stats()

    async def list_pending_ai(self, limit: int = 50) -> List[Call]:
        return await self._repo.list_pending_ai(limit=limit)

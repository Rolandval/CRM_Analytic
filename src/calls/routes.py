from datetime import datetime
from typing import Literal, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import CallState, CallType
from src.schemas.call import CallDetailOut, CallFilter, CallOut
from src.schemas.common import PaginatedResponse
from src.services.call_service import CallService
from src.services.export_service import export_calls

calls_router = APIRouter(prefix="/calls", tags=["Calls"])


@calls_router.get("", response_model=PaginatedResponse[CallOut])
async def list_calls(
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    call_type: Optional[CallType] = Query(None),
    call_state: Optional[CallState] = Query(None),
    user_id: Optional[int] = Query(None),
    min_duration: Optional[float] = Query(None, ge=0),
    max_duration: Optional[float] = Query(None, ge=0),
    callback: Optional[bool] = Query(None),
    search: Optional[str] = Query(None, max_length=50),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
):
    filters = CallFilter(
        date_from=date_from,
        date_to=date_to,
        call_type=call_type,
        call_state=call_state,
        user_id=user_id,
        min_duration=min_duration,
        max_duration=max_duration,
        callback=callback,
        search=search,
    )
    svc = CallService(session)
    calls, total = await svc.list_calls(filters, page=page, page_size=page_size)
    return PaginatedResponse.build(
        items=[CallOut.model_validate(c) for c in calls],
        total=total,
        page=page,
        page_size=page_size,
    )


@calls_router.get("/stats")
async def get_call_stats(session: AsyncSession = Depends(get_db)):
    return await CallService(session).get_stats()


@calls_router.get("/export")
async def export_calls_endpoint(
    format: Literal["csv", "xlsx", "txt"] = Query("csv"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    call_type: Optional[CallType] = Query(None),
    call_state: Optional[CallState] = Query(None),
    user_id: Optional[int] = Query(None),
    min_duration: Optional[float] = Query(None, ge=0),
    max_duration: Optional[float] = Query(None, ge=0),
    callback: Optional[bool] = Query(None),
    search: Optional[str] = Query(None, max_length=50),
    max_rows: int = Query(100_000, ge=1, le=500_000),
    session: AsyncSession = Depends(get_db),
):
    filters = CallFilter(
        date_from=date_from, date_to=date_to,
        call_type=call_type, call_state=call_state,
        user_id=user_id,
        min_duration=min_duration, max_duration=max_duration,
        callback=callback, search=search,
    )
    calls = await CallService(session).list_all_for_export(filters, max_rows=max_rows)
    content, mime, filename = export_calls(calls, format)
    return Response(
        content=content,
        media_type=mime,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


@calls_router.get("/{call_id}", response_model=CallDetailOut)
async def get_call(call_id: int, session: AsyncSession = Depends(get_db)):
    call = await CallService(session).get_call(call_id)
    return CallDetailOut.model_validate(call)

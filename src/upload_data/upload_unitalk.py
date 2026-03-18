"""
Unitalk API client — async version using httpx.

Key fixes vs original:
- Uses httpx.AsyncClient (non-blocking, works in async context)
- No API token printed to stdout
- Configurable URL, timeout, page size from settings
- Raises UnitalkAPIError on non-200 responses
- Uses proper timezone-aware datetime handling
"""
from datetime import datetime
from typing import Any, Dict, List

import httpx

from core.config import settings
from core.exceptions import UnitalkAPIError
from core.logging import get_logger

logger = get_logger(__name__)

PHONE_FIELDS = ("from_number", "to_number", "outer_number")


async def fetch_unitalk_calls(*, today: bool = False) -> List[Dict[str, Any]]:
    """
    Async generator-style fetcher: pages through the Unitalk API
    and returns all calls as a flat list.

    Args:
        today: If True, only fetch today's calls.

    Returns:
        List of normalised call dicts ready for DB insertion.
    """
    if today:
        date_from = datetime.now().strftime("%Y-%m-%d 00:00:00")
        date_to = datetime.now().strftime("%Y-%m-%d 23:59:59")
    else:
        date_from = settings.unitalk_sync_from_date
        date_to = datetime.now().strftime("%Y-%m-%d 23:59:59")

    headers = {
        "Authorization": f"Bearer {settings.api_token}",
        "Content-Type": "application/json",
    }

    all_calls: List[Dict[str, Any]] = []
    offset = 0
    total_count: int | None = None

    logger.info("unitalk_fetch_start", date_from=date_from, date_to=date_to)

    async with httpx.AsyncClient(timeout=settings.unitalk_request_timeout) as client:
        while total_count is None or offset < total_count:
            payload = {
                "dateFrom": date_from,
                "dateTo": date_to,
                "limit": settings.unitalk_page_size,
                "offset": offset,
            }

            logger.debug("unitalk_page_request", offset=offset, limit=settings.unitalk_page_size)

            try:
                response = await client.post(settings.unitalk_api_url, headers=headers, json=payload)
            except httpx.TimeoutException as exc:
                raise UnitalkAPIError(
                    f"Unitalk API timed out after {settings.unitalk_request_timeout}s",
                    detail=str(exc),
                )
            except httpx.RequestError as exc:
                raise UnitalkAPIError("Unitalk API connection error", detail=str(exc))

            if response.status_code != 200:
                raise UnitalkAPIError(
                    f"Unitalk API returned HTTP {response.status_code}",
                    detail=response.text[:500],
                )

            data = response.json()
            calls = data.get("calls", [])

            if total_count is None:
                total_count = data.get("count", 0)
                logger.info("unitalk_total_count", total=total_count)

            if not calls:
                logger.debug("unitalk_no_more_calls", offset=offset)
                break

            for raw in calls:
                call_data = _transform_call(raw)
                if call_data:
                    all_calls.append(call_data)

            offset += len(calls)
            logger.debug("unitalk_page_done", fetched=offset, total=total_count)

    logger.info("unitalk_fetch_complete", total_fetched=len(all_calls))
    return all_calls


def _transform_call(raw: Dict[str, Any]) -> Dict[str, Any] | None:
    """Map a raw Unitalk API call dict to our internal schema."""
    call_id = raw.get("id")
    if call_id is None:
        return None

    to_field = raw.get("to")
    to_number = to_field[0] if isinstance(to_field, list) and to_field else str(to_field or "")

    date_str = raw.get("date")
    call_date: datetime | None = None
    if date_str:
        try:
            call_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            logger.warning("unitalk_bad_date", call_id=call_id, date_str=date_str)

    return {
        "id": call_id,
        "from_number": str(raw.get("from") or ""),
        "to_number": to_number,
        "call_type": "IN" if raw.get("direction") == "IN" else "OUT",
        "call_state": raw.get("state", "NOANSWER"),
        "date": call_date,
        "seconds_fulltime": float(raw.get("secondsFullTime") or 0),
        "seconds_talktime": float(raw.get("secondsTalk") or 0),
        "mp3_link": raw.get("link"),
        "callback": bool(raw.get("callback", False)),
        # Extra fields used downstream for phone resolution
        "outer_number": raw.get("outerNumber"),
    }

"""
CallSyncService — orchestrates the full Unitalk → DB synchronisation pipeline.

Responsibilities (originally scattered across controllers.py):
1. Fetch raw call data from Unitalk (via async client)
2. Normalise phone numbers and determine the client phone
3. Upsert calls in the DB using bulk operations
4. Update user call counts using a single UPDATE query
5. Return structured statistics

Key improvements over original:
- Fully async (no blocking requests.post)
- Bulk upsert (no per-call SELECT + INSERT loop)
- Single-query call count update (no N+1)
- Calls processed in configurable batches (no single 10k-record transaction)
- Proper error isolation per batch (one bad batch doesn't lose all data)
"""
import re
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from core.logging import get_logger
from db.database import get_session
from db.models import CallState, CallType
from src.repositories.call_repository import CallRepository
from src.repositories.user_repository import UserRepository
from src.schemas.call import SyncStats
from src.upload_data.upload_unitalk import fetch_unitalk_calls

logger = get_logger(__name__)

# Minimum number of digits for a valid external phone number
_PHONE_MIN_DIGITS = 9
_BATCH_SIZE = 200  # Process calls in batches to limit transaction scope

_DIGITS_RE = re.compile(r"\d")


def _normalize_phone(number: Optional[str]) -> Optional[str]:
    """Extract digits; return None if fewer than _PHONE_MIN_DIGITS digits."""
    if not number:
        return None
    digits = "".join(_DIGITS_RE.findall(str(number)))
    return digits if len(digits) >= _PHONE_MIN_DIGITS else None


def _pick_client_phone(call_data: Dict[str, Any]) -> Optional[str]:
    """Determine the external (client) phone number from a call record."""
    call_type = call_data.get("call_type", "")
    from_n = call_data.get("from_number")
    to_n = call_data.get("to_number")
    outer_n = call_data.get("outer_number")

    if call_type == "IN":
        return _normalize_phone(from_n) or _normalize_phone(outer_n) or _normalize_phone(to_n)
    return _normalize_phone(to_n) or _normalize_phone(from_n) or _normalize_phone(outer_n)


def _map_call_type(val: str) -> CallType:
    return CallType.INB if val == "IN" else CallType.OUT


def _map_call_state(val: str) -> CallState:
    try:
        return CallState[val]
    except KeyError:
        logger.warning("unknown_call_state", value=val)
        return CallState.NOANSWER


async def _process_batch(
    batch: List[Dict[str, Any]],
) -> Tuple[int, int, int, int]:
    """
    Process a single batch of calls inside its own transaction.
    Returns (new, updated, skipped, errors).
    """
    new = updated = skipped = errors = 0

    async with get_session() as session:
        user_repo = UserRepository(session)
        call_repo = CallRepository(session)

        records_to_upsert: List[Dict] = []
        phone_cache: Dict[str, int] = {}

        for call_data in batch:
            try:
                phone = _pick_client_phone(call_data)
                if not phone:
                    skipped += 1
                    continue

                # Cache user lookups within the batch
                if phone not in phone_cache:
                    user, _ = await user_repo.get_or_create(phone)
                    phone_cache[phone] = user.id

                records_to_upsert.append({
                    "id": call_data["id"],
                    "user_id": phone_cache[phone],
                    "from_number": call_data.get("from_number"),
                    "to_number": call_data.get("to_number"),
                    "call_type": _map_call_type(call_data.get("call_type", "OUT")),
                    "call_state": _map_call_state(call_data.get("call_state", "NOANSWER")),
                    "date": call_data.get("date"),
                    "seconds_fulltime": call_data.get("seconds_fulltime", 0),
                    "seconds_talktime": call_data.get("seconds_talktime", 0),
                    "mp3_link": call_data.get("mp3_link"),
                    "callback": call_data.get("callback", False),
                })
            except Exception as exc:
                logger.error("call_processing_error", call_id=call_data.get("id"), error=str(exc))
                errors += 1

        if records_to_upsert:
            batch_new, batch_updated = await call_repo.bulk_upsert(records_to_upsert)
            new += batch_new
            updated += batch_updated

        # Update call counts after each batch (single UPDATE query)
        await user_repo.bulk_update_calls_count()

    return new, updated, skipped, errors


async def sync_calls(*, today: bool = False) -> SyncStats:
    """
    Main entry point: fetch from Unitalk and persist to DB.
    Called by API endpoints and the background scheduler.
    """
    logger.info("sync_start", today=today)

    raw_calls = await fetch_unitalk_calls(today=today)
    total = len(raw_calls)
    logger.info("sync_fetched", total=total)

    new = updated = skipped = errors = 0

    # Process in batches to limit transaction size and improve resilience
    for i in range(0, max(total, 1), _BATCH_SIZE):
        batch = raw_calls[i: i + _BATCH_SIZE]
        b_new, b_updated, b_skipped, b_errors = await _process_batch(batch)
        new += b_new
        updated += b_updated
        skipped += b_skipped
        errors += b_errors
        logger.info("sync_batch_done", batch_start=i, new=b_new, updated=b_updated)

    stats = SyncStats(
        total=total, new=new, updated=updated, skipped=skipped, errors=errors
    )
    logger.info("sync_complete", **stats.model_dump())
    return stats

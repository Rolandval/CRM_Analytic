"""
AiSyncService — оркеструє Selenium-парсер та збереження аналітики в БД.

Selenium є синхронним → запускається в ThreadPoolExecutor.
Матчинг дзвінків: from_number (останні 9 цифр) + call_date.
"""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select, or_

from core.config import settings
from core.exceptions import ExternalServiceError
from core.logging import get_logger
from db.database import get_session
from db.models import Call
from src.repositories.call_repository import CallRepository
from src.selenium_parser.unitalk_parser import CallAnalyticData, ParseStats, UnitalkParser

logger = get_logger(__name__)

_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="selenium")


@dataclass
class AnalyticsSyncStats:
    total_scraped: int = 0
    saved: int = 0
    skipped_no_data: int = 0
    skipped_no_match: int = 0
    errors: int = 0


# ── Selenium runner (sync, runs in thread) ─────────────────────────────────────

def _run_parser(today: bool) -> ParseStats:
    # from_date: беремо з конфігу ("2025-09-01 00:00:00" → "2025-09-01")
    raw_from = getattr(settings, "unitalk_sync_from_date", "2025-09-01 00:00:00")
    from_date = raw_from.split()[0] if raw_from else None  # "YYYY-MM-DD"

    parser = UnitalkParser(
        username=settings.unitalk_web_username,
        password=settings.unitalk_web_password,
        headless=settings.unitalk_parser_headless,
        page_load_timeout=settings.unitalk_parser_page_timeout,
        element_wait_timeout=settings.unitalk_parser_element_timeout,
    )
    try:
        parser.login()
        return parser.get_analytics(today=today, from_date=from_date)
    finally:
        parser.quit()


# ── DB matching ────────────────────────────────────────────────────────────────

async def _find_call_id(
    item: CallAnalyticData,
    session,
) -> Optional[int]:
    """
    Шукає Call.id у БД по номеру телефону + дата.

    Логіка: клієнтський номер з веб-парсера (web_from/web_to) може бути
    записаний у Call.from_number АБО Call.to_number залежно від напряму дзвінка:
      - Incoming: from_number=клієнт, to_number=лінія (4893 тощо)
      - Outgoing: from_number=лінія, to_number=клієнт

    Тому шукаємо кожен номер в обох колонках.
    """
    # Нормалізація: прибираємо + та ведучі нулі
    def normalize(n: str) -> str:
        return n.lstrip("+").lstrip("0")

    from_num = normalize(item.from_number)
    to_num = normalize(item.to_number)
    call_date = item.call_date  # "YYYY-MM-DD"

    if not call_date or (not from_num and not to_num):
        return None

    # Останні 9 цифр — достатньо для унікального матчингу по номеру
    tails = []
    for num in [from_num, to_num]:
        if len(num) >= 7:  # відкидаємо внутрішні короткі номери (4893, 7622)
            tails.append(num[-9:] if len(num) >= 9 else num)

    if not tails:
        return None

    # Весь день за датою
    date_from = datetime.strptime(call_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0)
    date_to = date_from.replace(hour=23, minute=59, second=59)

    # Шукаємо: номер може бути в from_number або to_number (обидва напрями)
    for tail in tails:
        result = await session.execute(
            select(Call.id)
            .where(
                or_(
                    Call.from_number.contains(tail),
                    Call.to_number.contains(tail),
                ),
                Call.date >= date_from,
                Call.date <= date_to,
            )
            .order_by(Call.date.asc())
            .limit(1)
        )
        found = result.scalar_one_or_none()
        if found:
            return found

    return None


# ── Main async service ─────────────────────────────────────────────────────────

async def sync_analytics(today: bool = False) -> AnalyticsSyncStats:
    """
    1. Запускає Selenium-парсер у окремому потоці.
    2. Для кожного результату знаходить Call у БД.
    3. Зберігає аналітику через CallRepository.upsert_ai_analytic().
    """
    stats = AnalyticsSyncStats()
    logger.info("ai_sync.start", today=today)

    # ── 1. Парсинг ─────────────────────────────────────────────────────────────
    try:
        loop = asyncio.get_event_loop()
        parse_result: ParseStats = await loop.run_in_executor(
            _executor, _run_parser, today
        )
    except Exception as exc:
        logger.error("ai_sync.parser_failed", error=str(exc))
        raise ExternalServiceError(
            message="Selenium-парсер Unitalk завершився з помилкою",
            detail=str(exc),
        )

    stats.total_scraped = parse_result.total
    stats.skipped_no_data = parse_result.skipped_no_analytics
    stats.errors = parse_result.errors

    # Беремо тільки успішні результати з хоча б одним заповненим полем
    items: List[CallAnalyticData] = [
        r for r in parse_result.results
        if r.parse_error is None and any([
            r.conversation_topic, r.key_points_of_the_dialogue, r.next_steps
        ])
    ]

    logger.info("ai_sync.parse_done", total=parse_result.total, with_data=len(items))

    if not items:
        return stats

    # ── 2. Збереження в БД ─────────────────────────────────────────────────────
    async with get_session() as session:
        repo = CallRepository(session)

        for item in items:
            try:
                call_id = await _find_call_id(item, session)

                if call_id is None:
                    stats.skipped_no_match += 1
                    logger.warning(
                        "ai_sync.no_match",
                        from_num=item.from_number,
                        to_num=item.to_number,
                        date=item.call_date,
                    )
                    continue

                await repo.upsert_ai_analytic(
                    call_id=call_id,
                    processing_status="done",
                    processed_at=datetime.now(timezone.utc),
                    conversation_topic=item.conversation_topic,
                    key_points_of_the_dialogue=item.key_points_of_the_dialogue,
                    next_steps=item.next_steps,
                    operator_errors=item.operator_errors,
                    keywords=item.keywords,
                    badwords=item.badwords,
                    attention_to_the_call=item.attention_to_the_call,
                    clients_mood=item.clients_mood,
                    operators_mood=item.operators_mood,
                    customer_satisfaction=item.customer_satisfaction,
                    operator_professionalism=item.operator_professionalism,
                    empathy=item.empathy,
                    clarity_of_communication=item.clarity_of_communication,
                    problem_identification=item.problem_identification,
                    involvement=item.involvement,
                    ability_to_adapt=item.ability_to_adapt,
                    problem_solving_efficiency=item.problem_solving_efficiency,
                    error_message=None,
                )
                stats.saved += 1
                logger.info(
                    "ai_sync.saved",
                    call_id=call_id,
                    topic=(item.conversation_topic or "")[:60],
                )

            except Exception as exc:
                stats.errors += 1
                logger.error("ai_sync.save_error", from_num=item.from_number, error=str(exc))

    logger.info(
        "ai_sync.done",
        today=today,
        total_scraped=stats.total_scraped,
        saved=stats.saved,
        skipped_no_data=stats.skipped_no_data,
        skipped_no_match=stats.skipped_no_match,
        errors=stats.errors,
    )
    return stats

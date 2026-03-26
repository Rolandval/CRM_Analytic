"""
Сервіс автоматичної категоризації користувачів через Gemini AI.

Алгоритм:
  1. Вибираємо users де category_id IS NULL або category_id = 1 (Default)
  2. Для кожного user підтягуємо всі CallAiAnalytic.conversation_topic
  3. Надсилаємо теми у Gemini — просимо визначити category_id
  4. Оновлюємо category_id у таблиці users
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sqlalchemy import or_, select, update

from db.database import get_session
from core.logging import get_logger
from db.models import Call, CallAiAnalytic, User
from src.ai.gemini_req import gemini_request

logger = get_logger(__name__)

# ── Категорії (id → назва) ─────────────────────────────────────────────────────

CATEGORIES = {
    1:  "Default",
    2:  "авто акб",
    3:  "інвертор",
    4:  "акумулятор lifepo4",
    5:  "панелі",
    6:  "кріплення",
    7:  "кабель",
    8:  "акумулятор agm-gel",
    9:  "ЕСС малі від 25 до 200Квт",
    10: "ЕСС великі від 200квт",
}

CATEGORIES_PROMPT_BLOCK = "\n".join(
    f"  {id_} — {name}" for id_, name in CATEGORIES.items()
)


# ── Результат ──────────────────────────────────────────────────────────────────

@dataclass
class CategorizationStats:
    total: int = 0
    categorized: int = 0
    skipped_no_topics: int = 0
    errors: int = 0
    results: list = field(default_factory=list)


# ── Запит до Gemini ────────────────────────────────────────────────────────────

def _build_prompt(phone: str, topics: List[str]) -> str:
    topics_block = "\n".join(f"  - {t}" for t in topics)
    return f"""Ти — асистент для категоризації клієнтів магазину акумуляторів та енергетичного обладнання.

Клієнт з номером {phone} має такі теми розмов з менеджерами:
{topics_block}

Визнач, до якої категорії відноситься цей клієнт:
{CATEGORIES_PROMPT_BLOCK}

Правила:
- Обери ОДНУ найбільш підходящу категорію
- Якщо тема явно про автомобільні акумулятори — category_id 2
- Якщо про інвертори — category_id 3
- Якщо про LiFePO4 — category_id 4
- Якщо про сонячні панелі — category_id 5
- Якщо про кріплення для панелей — category_id 6
- Якщо про кабелі — category_id 7
- Якщо про AGM/GEL акумулятори — category_id 8
- Якщо про системи зберігання енергії малі (25-200 кВт) — category_id 9
- Якщо про системи зберігання енергії великі (>200 кВт) — category_id 10
- Якщо незрозуміло або змішані теми — category_id 1 (Default)

Відповідь ТІЛЬКИ у форматі JSON:
{{"category_id": <число від 1 до 10>}}"""


# ── Основна функція ────────────────────────────────────────────────────────────

async def categorize_users() -> CategorizationStats:
    """
    Проходить по users з category_id IS NULL або = 1,
    бере conversation_topic їхніх дзвінків і через Gemini визначає категорію.
    """
    stats = CategorizationStats()

    async with get_session() as session:
        # 1. Вибираємо users без категорії або з Default
        result = await session.execute(
            select(User).where(
                or_(User.category_id.is_(None), User.category_id == 1)
            ).order_by(User.id)
        )
        users: List[User] = list(result.scalars().all())
        stats.total = len(users)

        logger.info("user_categorization.start", total=stats.total)

        for user in users:
            try:
                # 2. Збираємо conversation_topic з CallAiAnalytic через Call
                topics_result = await session.execute(
                    select(CallAiAnalytic.conversation_topic)
                    .join(Call, Call.id == CallAiAnalytic.call_id)
                    .where(
                        Call.user_id == user.id,
                        CallAiAnalytic.conversation_topic.is_not(None),
                        CallAiAnalytic.conversation_topic != "",
                    )
                )
                topics: List[str] = [t for (t,) in topics_result.all() if t]

                if not topics:
                    stats.skipped_no_topics += 1
                    logger.info("user_categorization.no_topics",
                                user_id=user.id, phone=user.phone_number)
                    continue

                # 3. Запит до Gemini
                prompt = _build_prompt(user.phone_number or str(user.id), topics)
                response = await _gemini_async(prompt)

                if not isinstance(response, dict) or "category_id" not in response:
                    logger.warning("user_categorization.bad_response",
                                   user_id=user.id, response=response)
                    stats.errors += 1
                    continue

                new_category_id: int = int(response["category_id"])
                if new_category_id not in CATEGORIES:
                    logger.warning("user_categorization.invalid_category",
                                   user_id=user.id, category_id=new_category_id)
                    stats.errors += 1
                    continue

                # 4. Оновлюємо category_id — прямий UPDATE без ORM flush
                # (уникає deadlock з bulk_update_calls_count)
                await session.execute(
                    update(User)
                    .where(User.id == user.id)
                    .values(category_id=new_category_id)
                    .execution_options(synchronize_session=False)
                )

                stats.categorized += 1
                stats.results.append({
                    "user_id": user.id,
                    "phone": user.phone_number,
                    "category_id": new_category_id,
                    "category_name": CATEGORIES[new_category_id],
                    "topics_count": len(topics),
                })
                logger.info("user_categorization.done",
                            user_id=user.id,
                            phone=user.phone_number,
                            category_id=new_category_id,
                            category=CATEGORIES[new_category_id])

            except Exception as exc:
                logger.error("user_categorization.error",
                             user_id=getattr(user, 'id', '?'), error=str(exc))
                stats.errors += 1
                # Відновлюємо сесію після помилки flush/deadlock
                try:
                    await session.rollback()
                except Exception:
                    pass

    logger.info("user_categorization.complete",
                total=stats.total,
                categorized=stats.categorized,
                skipped_no_topics=stats.skipped_no_topics,
                errors=stats.errors)
    return stats


# ── Обгортка для async виклику gemini_request ─────────────────────────────────

async def _gemini_async(prompt: str):
    """gemini_request вже async — просто викликаємо."""
    return await gemini_request(prompt)

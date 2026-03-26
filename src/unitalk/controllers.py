from src.upload_data.upload_unitalk import get_unitalk_all_data
from src.helpers.user import get_or_create_user
from db.database import get_session
from db.models import Call, CallType, CallState, User
from sqlalchemy import select, update
from typing import Dict, List


def _normalize_phone(number: str | None) -> str | None:
    """Повертає тільки цифри, якщо номер схожий на зовнішній (>=9 цифр). Інакше None."""
    if not number:
        return None
    digits = "".join(ch for ch in str(number) if ch.isdigit())
    return digits if len(digits) >= 9 else None


def _pick_client_phone(call_data: Dict) -> str | None:
    """Обирає клієнтський номер з даних дзвінка (ігноруючи внутрішні розширення типу 7622)."""
    call_type = call_data.get("call_type")
    from_number = call_data.get("from_number")
    to_number = call_data.get("to_number")
    outer_number = call_data.get("outer_number")

    # Для вхідних спочатку беремо "from", потім outer/to
    if call_type == "IN":
        return (
            _normalize_phone(from_number)
            or _normalize_phone(outer_number)
            or _normalize_phone(to_number)
        )

    # Для вихідних спочатку беремо "to", потім from/outer
    return (
        _normalize_phone(to_number)
        or _normalize_phone(from_number)
        or _normalize_phone(outer_number)
    )


async def _save_calls_to_db(calls_data: List[Dict]) -> Dict[str, int]:
    """
    Зберігає дзвінки в базу даних.
    Повертає статистику: кількість нових, оновлених та пропущених записів.
    """
    stats = {
        "total": len(calls_data),
        "new": 0,
        "updated": 0,
        "skipped": 0,
        "errors": 0
    }
    
    async with get_session() as session:
        for call_data in calls_data:
            try:
                # Визначаємо номер телефону клієнта (зовнішній номер)
                phone_number = _pick_client_phone(call_data)
                
                if not phone_number:
                    stats["skipped"] += 1
                    continue
                
                # Отримуємо або створюємо користувача
                user_id = await get_or_create_user(phone_number, session)
                
                # Перевіряємо, чи існує вже такий дзвінок
                result = await session.execute(
                    select(Call).where(Call.id == call_data.get("id"))
                )
                existing_call = result.scalar_one_or_none()
                
                # Мапимо CallType
                call_type_str = call_data.get("call_type", "IN")
                call_type = CallType.INB if call_type_str == "IN" else CallType.OUT
                
                # Мапимо CallState
                call_state_str = call_data.get("call_state", "NOANSWER")
                try:
                    call_state = CallState[call_state_str]
                except KeyError:
                    call_state = CallState.NOANSWER
                
                if existing_call:
                    # Оновлюємо існуючий запис
                    existing_call.user_id = user_id
                    existing_call.from_number = call_data.get("from_number")
                    existing_call.to_number = call_data.get("to_number")
                    existing_call.call_type = call_type
                    existing_call.call_state = call_state
                    existing_call.date = call_data.get("date")
                    existing_call.seconds_fulltime = call_data.get("seconds_fulltime", 0)
                    existing_call.seconds_talktime = call_data.get("seconds_talktime", 0)
                    existing_call.mp3_link = call_data.get("mp3_link")
                    existing_call.callback = call_data.get("callback", False)
                    
                    stats["updated"] += 1
                else:
                    # Створюємо новий запис
                    new_call = Call(
                        id=call_data.get("id"),
                        user_id=user_id,
                        from_number=call_data.get("from_number"),
                        to_number=call_data.get("to_number"),
                        call_type=call_type,
                        call_state=call_state,
                        date=call_data.get("date"),
                        seconds_fulltime=call_data.get("seconds_fulltime", 0),
                        seconds_talktime=call_data.get("seconds_talktime", 0),
                        mp3_link=call_data.get("mp3_link"),
                        callback=call_data.get("callback", False)
                    )
                    session.add(new_call)
                    stats["new"] += 1
                    
            except Exception as e:
                print(f"❌ Помилка при обробці дзвінка {call_data.get('id')}: {e}")
                # Повертаємо сесію у валідний стан і продовжуємо
                try:
                    await session.rollback()
                except Exception:
                    pass
                stats["errors"] += 1
                continue
        
        # Оновлюємо лічильник дзвінків для всіх користувачів
        await _update_users_call_count(session)
    
    return stats


async def _update_users_call_count(session):
    """
    Оновлює лічильник дзвінків для всіх користувачів.
    """
    # Отримуємо всіх користувачів
    result = await session.execute(select(User))
    users = result.scalars().all()
    
    for user in users:
        # Підраховуємо кількість дзвінків для користувача
        call_count_result = await session.execute(
            select(Call).where(Call.user_id == user.id)
        )
        calls = call_count_result.scalars().all()
        user.calls_count = len(calls)


async def upload_calls_all() -> Dict[str, int]:
    """
    Завантажує всі дзвінки з 1 вересня 2021 року до поточної дати.
    Повертає статистику завантаження.
    """
    print("📞 Завантаження всіх дзвінків з Unitalk...")
    calls_data = get_unitalk_all_data(today=False)  # Синхронний виклик
    print(f"✅ Отримано {len(calls_data)} записів з API")
    
    stats = await _save_calls_to_db(calls_data)
    
    print(f"""
    📊 Статистика завантаження:
    - Всього отримано: {stats['total']}
    - Нових записів: {stats['new']}
    - Оновлено: {stats['updated']}
    - Пропущено: {stats['skipped']}
    - Помилок: {stats['errors']}
    """)
    
    return stats


async def upload_calls_today() -> Dict[str, int]:
    """
    Завантажує дзвінки за сьогоднішній день.
    Повертає статистику завантаження.
    """
    print("📞 Завантаження дзвінків за сьогодні...")
    calls_data = get_unitalk_all_data(today=True)  # Синхронний виклик
    print(f"✅ Отримано {len(calls_data)} записів з API")
    
    stats = await _save_calls_to_db(calls_data)
    
    print(f"""
    📊 Статистика завантаження:
    - Всього отримано: {stats['total']}
    - Нових записів: {stats['new']}
    - Оновлено: {stats['updated']}
    - Пропущено: {stats['skipped']}
    - Помилок: {stats['errors']}
    """)
    
    return stats

from db.database import get_session
from db.models import User
from sqlalchemy import select


async def get_or_create_user(phone_number: str, session) -> int:
    """
    Get existing user by phone number or create a new one.
    Returns user_id.
    """
    # Шукаємо користувача за номером телефону
    result = await session.execute(
        select(User).where(User.phone_number == phone_number)
    )
    user = result.scalar_one_or_none()
    
    if user:
        return user.id
    
    # Створюємо нового користувача
    user = User(phone_number=phone_number)
    session.add(user)
    await session.flush()  # Отримуємо ID перед commit
    
    return user.id
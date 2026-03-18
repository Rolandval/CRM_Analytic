"""
JWT Authentication service.

Handles password hashing, token creation/verification,
and admin user management.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.exceptions import AuthenticationError, InvalidCredentials, TokenExpired
from core.logging import get_logger
from db.models import AdminUser

logger = get_logger(__name__)

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def create_access_token(subject: str, extra: dict | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        **(extra or {}),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenExpired("Access token has expired")
    except JWTError as exc:
        raise AuthenticationError("Could not validate token", detail=str(exc))


# ── DB operations ─────────────────────────────────────────────────────────────

async def get_admin_by_username(session: AsyncSession, username: str) -> Optional[AdminUser]:
    result = await session.execute(
        select(AdminUser).where(AdminUser.username == username, AdminUser.is_active.is_(True))
    )
    return result.scalar_one_or_none()


async def get_admin_by_id(session: AsyncSession, admin_id: int) -> Optional[AdminUser]:
    result = await session.execute(
        select(AdminUser).where(AdminUser.id == admin_id, AdminUser.is_active.is_(True))
    )
    return result.scalar_one_or_none()


async def authenticate(session: AsyncSession, username: str, password: str) -> AdminUser:
    admin = await get_admin_by_username(session, username)
    if not admin or not verify_password(password, admin.hashed_password):
        raise InvalidCredentials("Incorrect username or password")

    # Track last login
    admin.last_login = datetime.now(timezone.utc)
    await session.flush()

    logger.info("admin_login", username=username)
    return admin


async def create_admin(
    session: AsyncSession,
    username: str,
    email: str,
    password: str,
    is_superuser: bool = False,
) -> AdminUser:
    admin = AdminUser(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        is_superuser=is_superuser,
    )
    session.add(admin)
    await session.flush()
    logger.info("admin_created", username=username)
    return admin

"""
FastAPI dependency functions for authentication.

Usage in a route:
    @router.get("/protected")
    async def protected(current_admin: AdminUser = Depends(require_auth)):
        ...

For superuser-only routes:
    @router.delete("/admin-only")
    async def admin_only(current_admin: AdminUser = Depends(require_superuser)):
        ...
"""
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.exceptions import AuthenticationError, PermissionDenied
from db.database import get_db
from db.models import AdminUser
from src.auth.service import decode_token, get_admin_by_id
from sqlalchemy.ext.asyncio import AsyncSession

_bearer = HTTPBearer(auto_error=False)


async def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: AsyncSession = Depends(get_db),
) -> AdminUser:
    if not credentials:
        raise AuthenticationError("Missing authorization header")

    payload = decode_token(credentials.credentials)
    admin_id_str = payload.get("sub")
    if not admin_id_str:
        raise AuthenticationError("Invalid token payload")

    try:
        admin_id = int(admin_id_str)
    except (TypeError, ValueError):
        raise AuthenticationError("Invalid token subject")

    admin = await get_admin_by_id(session, admin_id)
    if not admin:
        raise AuthenticationError("User not found or deactivated")

    return admin


async def require_superuser(
    current_admin: AdminUser = Depends(require_auth),
) -> AdminUser:
    if not current_admin.is_superuser:
        raise PermissionDenied("Superuser access required")
    return current_admin

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from db.database import get_db
from db.models import AdminUser
from src.auth.dependencies import require_auth, require_superuser
from src.auth.service import authenticate, create_access_token, create_admin
from src.schemas.auth import AdminUserCreate, AdminUserOut, LoginRequest, TokenResponse

auth_router = APIRouter(prefix="/auth", tags=["Auth"])


@auth_router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    session: AsyncSession = Depends(get_db),
):
    """Authenticate and receive a JWT access token."""
    admin = await authenticate(session, data.username, data.password)
    token = create_access_token(
        subject=str(admin.id),
        extra={"username": admin.username, "superuser": admin.is_superuser},
    )
    return TokenResponse(
        access_token=token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@auth_router.get("/me", response_model=AdminUserOut)
async def get_me(current_admin: AdminUser = Depends(require_auth)):
    """Return the currently authenticated admin profile."""
    return current_admin


@auth_router.post(
    "/register",
    response_model=AdminUserOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_superuser)],
)
async def register_admin(
    data: AdminUserCreate,
    session: AsyncSession = Depends(get_db),
):
    """Create a new admin account (superuser only)."""
    admin = await create_admin(
        session,
        username=data.username,
        email=data.email,
        password=data.password,
        is_superuser=data.is_superuser,
    )
    return admin

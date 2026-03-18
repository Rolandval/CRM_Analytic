from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from src.schemas.common import PaginatedResponse
from src.schemas.user import (
    UserCategoryCreate,
    UserCategoryOut,
    UserCreate,
    UserListOut,
    UserOut,
    UserTypeCreate,
    UserTypeOut,
    UserUpdate,
)
from src.services.user_service import UserService

users_router = APIRouter(prefix="/users", tags=["Users"])


@users_router.get("", response_model=PaginatedResponse[UserListOut])
async def list_users(
    category_id: Optional[int] = Query(None),
    type_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
):
    svc = UserService(session)
    users, total = await svc.list_users(
        category_id=category_id,
        type_id=type_id,
        search=search,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse.build(
        items=[UserListOut.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
    )


@users_router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(data: UserCreate, session: AsyncSession = Depends(get_db)):
    return UserOut.model_validate(await UserService(session).create_user(data))


@users_router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: int, session: AsyncSession = Depends(get_db)):
    return UserOut.model_validate(await UserService(session).get_user(user_id))


@users_router.patch("/{user_id}", response_model=UserOut)
async def update_user(user_id: int, data: UserUpdate, session: AsyncSession = Depends(get_db)):
    return UserOut.model_validate(await UserService(session).update_user(user_id, data))


# ── Categories ────────────────────────────────────────────────────────────────

@users_router.get("/categories/list", response_model=list[UserCategoryOut])
async def list_categories(session: AsyncSession = Depends(get_db)):
    return [UserCategoryOut.model_validate(c) for c in await UserService(session).list_categories()]


@users_router.post("/categories", response_model=UserCategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(data: UserCategoryCreate, session: AsyncSession = Depends(get_db)):
    return UserCategoryOut.model_validate(await UserService(session).create_category(data.name))


# ── Types ─────────────────────────────────────────────────────────────────────

@users_router.get("/types/list", response_model=list[UserTypeOut])
async def list_types(session: AsyncSession = Depends(get_db)):
    return [UserTypeOut.model_validate(t) for t in await UserService(session).list_types()]


@users_router.post("/types", response_model=UserTypeOut, status_code=status.HTTP_201_CREATED)
async def create_type(data: UserTypeCreate, session: AsyncSession = Depends(get_db)):
    return UserTypeOut.model_validate(await UserService(session).create_type(data.name))

from typing import Literal, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from src.schemas.common import PaginatedResponse
from src.schemas.user import (
    UserCategoryCreate,
    UserCategoryOut,
    UserCategoryUpdate,
    UserCreate,
    UserListOut,
    UserOut,
    UserTypeCreate,
    UserTypeOut,
    UserTypeUpdate,
    UserUpdate,
)
from src.services.export_service import export_users
from src.services.user_service import UserService

users_router = APIRouter(prefix="/users", tags=["Users"])


@users_router.get("", response_model=PaginatedResponse[UserListOut])
async def list_users(
    category_id: Optional[int] = Query(None),
    type_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None, max_length=100),
    has_analytics: Optional[bool] = Query(None),
    sort_by: str = Query("id", pattern="^(id|name|phone_number|calls_count|created_at)$"),
    sort_order: Literal["asc", "desc"] = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
):
    svc = UserService(session)
    users, total = await svc.list_users(
        category_id=category_id,
        type_id=type_id,
        search=search,
        has_analytics=has_analytics,
        sort_by=sort_by,
        sort_order=sort_order,
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


@users_router.get("/export")
async def export_users_endpoint(
    format: Literal["csv", "xlsx", "txt"] = Query("csv"),
    category_id: Optional[int] = Query(None),
    type_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None, max_length=100),
    has_analytics: Optional[bool] = Query(None),
    sort_by: str = Query("id", pattern="^(id|name|phone_number|calls_count|created_at)$"),
    sort_order: Literal["asc", "desc"] = Query("desc"),
    max_rows: int = Query(100_000, ge=1, le=500_000),
    session: AsyncSession = Depends(get_db),
):
    users = await UserService(session).list_all_for_export(
        category_id=category_id,
        type_id=type_id,
        search=search,
        has_analytics=has_analytics,
        sort_by=sort_by,
        sort_order=sort_order,
        max_rows=max_rows,
    )
    content, mime, filename = export_users(users, format)
    return Response(
        content=content,
        media_type=mime,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


@users_router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: int, session: AsyncSession = Depends(get_db)):
    return UserOut.model_validate(await UserService(session).get_user(user_id))


@users_router.patch("/{user_id}", response_model=UserOut)
async def update_user(user_id: int, data: UserUpdate, session: AsyncSession = Depends(get_db)):
    return UserOut.model_validate(await UserService(session).update_user(user_id, data))


@users_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, session: AsyncSession = Depends(get_db)):
    await UserService(session).delete_user(user_id)


# ── Categories ────────────────────────────────────────────────────────────────

@users_router.get("/categories/list", response_model=list[UserCategoryOut])
async def list_categories(session: AsyncSession = Depends(get_db)):
    return [UserCategoryOut.model_validate(c) for c in await UserService(session).list_categories()]


@users_router.post("/categories", response_model=UserCategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(data: UserCategoryCreate, session: AsyncSession = Depends(get_db)):
    return UserCategoryOut.model_validate(await UserService(session).create_category(data.name))


@users_router.patch("/categories/{category_id}", response_model=UserCategoryOut)
async def update_category(category_id: int, data: UserCategoryUpdate, session: AsyncSession = Depends(get_db)):
    return UserCategoryOut.model_validate(await UserService(session).update_category(category_id, data.name))


@users_router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: int, session: AsyncSession = Depends(get_db)):
    await UserService(session).delete_category(category_id)


# ── Types ─────────────────────────────────────────────────────────────────────

@users_router.get("/types/list", response_model=list[UserTypeOut])
async def list_types(session: AsyncSession = Depends(get_db)):
    return [UserTypeOut.model_validate(t) for t in await UserService(session).list_types()]


@users_router.post("/types", response_model=UserTypeOut, status_code=status.HTTP_201_CREATED)
async def create_type(data: UserTypeCreate, session: AsyncSession = Depends(get_db)):
    return UserTypeOut.model_validate(await UserService(session).create_type(data.name))


@users_router.patch("/types/{type_id}", response_model=UserTypeOut)
async def update_type(type_id: int, data: UserTypeUpdate, session: AsyncSession = Depends(get_db)):
    return UserTypeOut.model_validate(await UserService(session).update_type(type_id, data.name))


@users_router.delete("/types/{type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_type(type_id: int, session: AsyncSession = Depends(get_db)):
    await UserService(session).delete_type(type_id)

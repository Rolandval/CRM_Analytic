"""User service — business logic on top of UserRepository."""
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ConflictError, NotFoundError, UserNotFound
from core.logging import get_logger
from db.models import User, UserCategory, UserType
from src.repositories.user_repository import UserRepository
from src.schemas.user import UserCreate, UserUpdate

logger = get_logger(__name__)


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = UserRepository(session)
        self._session = session

    async def get_user(self, user_id: int) -> User:
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise UserNotFound(f"User {user_id} not found")
        return user

    async def list_users(
        self,
        *,
        category_id: Optional[int] = None,
        type_id: Optional[int] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[User], int]:
        offset = (page - 1) * page_size
        return await self._repo.list_with_filters(
            category_id=category_id,
            type_id=type_id,
            search=search,
            offset=offset,
            limit=page_size,
        )

    async def create_user(self, data: UserCreate) -> User:
        if data.phone_number:
            existing = await self._repo.get_by_phone(data.phone_number)
            if existing:
                raise ConflictError(
                    f"User with phone {data.phone_number} already exists"
                )
        user = User(
            phone_number=data.phone_number,
            name=data.name,
            description=data.description,
            category_id=data.category_id,
        )
        self._session.add(user)
        await self._session.flush()
        logger.info("user_created", user_id=user.id, phone=data.phone_number)
        return user

    async def update_user(self, user_id: int, data: UserUpdate) -> User:
        user = await self.get_user(user_id)

        update_fields = data.model_dump(exclude_none=True, exclude={"type_ids"})
        for k, v in update_fields.items():
            setattr(user, k, v)

        if data.type_ids is not None:
            types = []
            for tid in data.type_ids:
                t = await self._repo.get_type(tid)
                if not t:
                    raise NotFoundError(f"UserType {tid} not found")
                types.append(t)
            user.types = types

        await self._session.flush()
        logger.info("user_updated", user_id=user_id)
        return user

    # ── Categories ────────────────────────────────────────────────────────────

    async def list_categories(self) -> List[UserCategory]:
        return await self._repo.list_categories()

    async def create_category(self, name: str) -> UserCategory:
        cat = await self._repo.create_category(name)
        logger.info("category_created", name=name)
        return cat

    # ── Types ─────────────────────────────────────────────────────────────────

    async def list_types(self) -> List[UserType]:
        return await self._repo.list_types()

    async def create_type(self, name: str) -> UserType:
        t = await self._repo.create_type(name)
        logger.info("user_type_created", name=name)
        return t

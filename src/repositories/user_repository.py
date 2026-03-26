"""
UserRepository — all DB queries for User / UserCategory / UserType.

Rules:
- No business logic here, only query building and execution.
- All methods accept an AsyncSession and return ORM objects or scalars.
- No session management (commit/rollback) — that is the service's responsibility.
"""
from typing import List, Literal, Optional, Tuple
from sqlalchemy import asc, delete, desc, exists, func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Call, CallAiAnalytic, User, UserCategory, UserType, user_type_association


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    # ── User ──────────────────────────────────────────────────────────────────

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self._s.execute(
            select(User)
            .options(selectinload(User.category), selectinload(User.types))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> Optional[User]:
        result = await self._s.execute(
            select(User).where(User.phone_number == phone)
        )
        return result.scalar_one_or_none()

    async def create(self, phone_number: str) -> User:
        user = User(phone_number=phone_number)
        self._s.add(user)
        await self._s.flush()
        return user

    async def get_or_create(self, phone_number: str) -> Tuple[User, bool]:
        """
        Атомарний INSERT ... ON CONFLICT DO NOTHING + SELECT.
        Безпечний для конкурентних воркерів (race condition-safe).
        """
        stmt = (
            pg_insert(User)
            .values(phone_number=phone_number)
            .on_conflict_do_nothing(index_elements=["phone_number"])
        )
        result = await self._s.execute(stmt)
        created = result.rowcount > 0
        user = await self.get_by_phone(phone_number)
        return user, created

    async def update(self, user: User, **fields) -> User:
        for k, v in fields.items():
            setattr(user, k, v)
        await self._s.flush()
        return user

    async def delete(self, user_id: int) -> bool:
        result = await self._s.execute(
            delete(User).where(User.id == user_id)
        )
        return result.rowcount > 0

    async def list_with_filters(
        self,
        *,
        category_id: Optional[int] = None,
        type_id: Optional[int] = None,
        search: Optional[str] = None,
        has_analytics: Optional[bool] = None,
        sort_by: str = "id",
        sort_order: Literal["asc", "desc"] = "desc",
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[User], int]:
        base_q = (
            select(User)
            .options(selectinload(User.category), selectinload(User.types))
        )
        count_q = select(func.count()).select_from(User)

        if category_id is not None:
            base_q = base_q.where(User.category_id == category_id)
            count_q = count_q.where(User.category_id == category_id)

        if type_id is not None:
            base_q = base_q.join(
                user_type_association,
                User.id == user_type_association.c.user_id
            ).where(user_type_association.c.type_id == type_id)
            count_q = count_q.join(
                user_type_association,
                User.id == user_type_association.c.user_id
            ).where(user_type_association.c.type_id == type_id)

        if search:
            pattern = f"%{search}%"
            base_q = base_q.where(
                User.phone_number.ilike(pattern) | User.name.ilike(pattern)
            )
            count_q = count_q.where(
                User.phone_number.ilike(pattern) | User.name.ilike(pattern)
            )

        if has_analytics is True:
            analytics_subq = (
                select(CallAiAnalytic.call_id)
                .join(Call, Call.id == CallAiAnalytic.call_id)
                .where(Call.user_id == User.id)
                .correlate(User)
                .exists()
            )
            base_q = base_q.where(analytics_subq)
            count_q = count_q.where(analytics_subq)
        elif has_analytics is False:
            analytics_subq = (
                select(CallAiAnalytic.call_id)
                .join(Call, Call.id == CallAiAnalytic.call_id)
                .where(Call.user_id == User.id)
                .correlate(User)
                .exists()
            )
            base_q = base_q.where(~analytics_subq)
            count_q = count_q.where(~analytics_subq)

        # Sort column mapping
        sort_col_map = {
            "id": User.id,
            "name": User.name,
            "phone_number": User.phone_number,
            "calls_count": User.calls_count,
            "created_at": User.created_at,
        }
        sort_col = sort_col_map.get(sort_by, User.id)
        order_fn = desc if sort_order == "desc" else asc

        total = (await self._s.execute(count_q)).scalar_one()
        users = (
            await self._s.execute(
                base_q.order_by(order_fn(sort_col)).offset(offset).limit(limit)
            )
        ).scalars().all()

        return list(users), total

    async def bulk_update_calls_count(self) -> None:
        """
        Single-query update of calls_count for ALL users.
        Replaces the N+1 loop that was in the original code.
        """
        await self._s.execute(
            update(User).values(
                calls_count=select(func.count())
                .where(User.id == User.id)  # correlated sub‑select placeholder
                .scalar_subquery()
            )
        )
        # More correct approach using a correlated subquery:
        from sqlalchemy import literal_column
        from db.models import Call

        subq = (
            select(func.count(Call.id))
            .where(Call.user_id == User.id)
            .correlate(User)
            .scalar_subquery()
        )
        await self._s.execute(update(User).values(calls_count=subq))

    # ── UserCategory ──────────────────────────────────────────────────────────

    async def list_categories(self) -> List[UserCategory]:
        result = await self._s.execute(select(UserCategory).order_by(UserCategory.name))
        return list(result.scalars().all())

    async def get_category(self, category_id: int) -> Optional[UserCategory]:
        result = await self._s.execute(
            select(UserCategory).where(UserCategory.id == category_id)
        )
        return result.scalar_one_or_none()

    async def create_category(self, name: str) -> UserCategory:
        cat = UserCategory(name=name)
        self._s.add(cat)
        await self._s.flush()
        return cat

    async def update_category(self, category_id: int, name: str) -> Optional[UserCategory]:
        cat = await self.get_category(category_id)
        if not cat:
            return None
        cat.name = name
        await self._s.flush()
        return cat

    async def delete_category(self, category_id: int) -> bool:
        result = await self._s.execute(
            delete(UserCategory).where(UserCategory.id == category_id)
        )
        return result.rowcount > 0

    # ── UserType ──────────────────────────────────────────────────────────────

    async def list_types(self) -> List[UserType]:
        result = await self._s.execute(select(UserType).order_by(UserType.name))
        return list(result.scalars().all())

    async def get_type(self, type_id: int) -> Optional[UserType]:
        result = await self._s.execute(select(UserType).where(UserType.id == type_id))
        return result.scalar_one_or_none()

    async def create_type(self, name: str) -> UserType:
        t = UserType(name=name)
        self._s.add(t)
        await self._s.flush()
        return t

    async def update_type(self, type_id: int, name: str) -> Optional[UserType]:
        t = await self.get_type(type_id)
        if not t:
            return None
        t.name = name
        await self._s.flush()
        return t

    async def delete_type(self, type_id: int) -> bool:
        result = await self._s.execute(
            delete(UserType).where(UserType.id == type_id)
        )
        return result.rowcount > 0

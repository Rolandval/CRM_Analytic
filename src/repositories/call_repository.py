"""
CallRepository — all DB queries for Call and CallAiAnalytic.
"""
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Call, CallAiAnalytic, CallState, CallType
from src.schemas.call import CallFilter


class CallRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    # ── Single call ────────────────────────────────────────────────────────────

    async def get_by_id(self, call_id: int) -> Optional[Call]:
        result = await self._s.execute(
            select(Call)
            .options(
                selectinload(Call.user),
                selectinload(Call.ai_analytic),
            )
            .where(Call.id == call_id)
        )
        return result.scalar_one_or_none()

    async def exists(self, call_id: int) -> bool:
        result = await self._s.execute(
            select(func.count()).select_from(Call).where(Call.id == call_id)
        )
        return result.scalar_one() > 0

    # ── List / filter ─────────────────────────────────────────────────────────

    async def list_with_filters(
        self,
        f: CallFilter,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Call], int]:
        base_q = (
            select(Call)
            .options(selectinload(Call.user))
        )
        count_q = select(func.count()).select_from(Call)

        if f.date_from:
            base_q = base_q.where(Call.date >= f.date_from)
            count_q = count_q.where(Call.date >= f.date_from)
        if f.date_to:
            base_q = base_q.where(Call.date <= f.date_to)
            count_q = count_q.where(Call.date <= f.date_to)
        if f.call_type:
            base_q = base_q.where(Call.call_type == f.call_type)
            count_q = count_q.where(Call.call_type == f.call_type)
        if f.call_state:
            base_q = base_q.where(Call.call_state == f.call_state)
            count_q = count_q.where(Call.call_state == f.call_state)
        if f.user_id is not None:
            base_q = base_q.where(Call.user_id == f.user_id)
            count_q = count_q.where(Call.user_id == f.user_id)
        if f.min_duration is not None:
            base_q = base_q.where(Call.seconds_talktime >= f.min_duration)
            count_q = count_q.where(Call.seconds_talktime >= f.min_duration)
        if f.max_duration is not None:
            base_q = base_q.where(Call.seconds_talktime <= f.max_duration)
            count_q = count_q.where(Call.seconds_talktime <= f.max_duration)
        if f.callback is not None:
            base_q = base_q.where(Call.callback == f.callback)
            count_q = count_q.where(Call.callback == f.callback)
        if f.search:
            pattern = f"%{f.search}%"
            base_q = base_q.where(
                Call.from_number.ilike(pattern) | Call.to_number.ilike(pattern)
            )
            count_q = count_q.where(
                Call.from_number.ilike(pattern) | Call.to_number.ilike(pattern)
            )

        total = (await self._s.execute(count_q)).scalar_one()
        calls = (
            await self._s.execute(
                base_q.order_by(Call.date.desc().nullslast()).offset(offset).limit(limit)
            )
        ).scalars().all()

        return list(calls), total

    # ── Upsert ─────────────────────────────────────────────────────────────────

    async def upsert(self, call_data: Dict) -> Tuple[bool, bool]:
        """
        PostgreSQL upsert via INSERT … ON CONFLICT DO UPDATE.
        Returns (is_new, success).
        """
        stmt = (
            pg_insert(Call)
            .values(**call_data)
            .on_conflict_do_update(
                index_elements=["id"],
                set_={
                    k: call_data[k]
                    for k in call_data
                    if k != "id"
                },
            )
        )
        result = await self._s.execute(stmt)
        # rowcount == 1 always; detect new vs updated via returned id
        is_new = result.rowcount == 1 and result.inserted_primary_key is not None
        return is_new, True

    async def bulk_upsert(self, records: List[Dict]) -> Tuple[int, int]:
        """
        Bulk upsert using a single executemany call.
        Returns (new_count, updated_count) — approximate via total vs pre-existing count.
        """
        if not records:
            return 0, 0

        ids = [r["id"] for r in records]
        existing_ids_result = await self._s.execute(
            select(Call.id).where(Call.id.in_(ids))
        )
        existing_ids = set(existing_ids_result.scalars().all())

        for record in records:
            stmt = (
                pg_insert(Call)
                .values(**record)
                .on_conflict_do_update(
                    index_elements=["id"],
                    set_={k: record[k] for k in record if k != "id"},
                )
            )
            await self._s.execute(stmt)

        new_count = len([r for r in records if r["id"] not in existing_ids])
        updated_count = len(records) - new_count
        return new_count, updated_count

    # ── Statistics ─────────────────────────────────────────────────────────────

    async def get_stats(self) -> Dict:
        total = (await self._s.execute(select(func.count()).select_from(Call))).scalar_one()

        by_type = (
            await self._s.execute(
                select(Call.call_type, func.count().label("cnt"))
                .group_by(Call.call_type)
            )
        ).all()

        by_state = (
            await self._s.execute(
                select(Call.call_state, func.count().label("cnt"))
                .group_by(Call.call_state)
            )
        ).all()

        avg_duration = (
            await self._s.execute(
                select(func.avg(Call.seconds_talktime))
                .where(Call.call_state == CallState.ANSWER)
            )
        ).scalar_one()

        return {
            "total": total,
            "by_type": {str(row.call_type): row.cnt for row in by_type},
            "by_state": {str(row.call_state): row.cnt for row in by_state},
            "avg_talk_duration_seconds": round(float(avg_duration or 0), 1),
        }

    # ── CallAiAnalytic ─────────────────────────────────────────────────────────

    async def get_ai_analytic(self, call_id: int) -> Optional[CallAiAnalytic]:
        result = await self._s.execute(
            select(CallAiAnalytic).where(CallAiAnalytic.call_id == call_id)
        )
        return result.scalar_one_or_none()

    async def upsert_ai_analytic(self, call_id: int, **fields) -> CallAiAnalytic:
        analytic = await self.get_ai_analytic(call_id)
        if analytic is None:
            analytic = CallAiAnalytic(call_id=call_id, **fields)
            self._s.add(analytic)
        else:
            for k, v in fields.items():
                setattr(analytic, k, v)
        await self._s.flush()
        return analytic

    async def list_pending_ai(self, limit: int = 50) -> List[Call]:
        """Return answered calls that do not yet have an AI analytic record (or are pending)."""
        result = await self._s.execute(
            select(Call)
            .outerjoin(CallAiAnalytic, Call.id == CallAiAnalytic.call_id)
            .where(
                Call.call_state == CallState.ANSWER,
                Call.mp3_link.isnot(None),
                (CallAiAnalytic.id.is_(None)) | (CallAiAnalytic.processing_status == "pending"),
            )
            .limit(limit)
        )
        return list(result.scalars().all())

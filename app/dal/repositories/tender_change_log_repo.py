from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dal.models.db_models import TenderStatusChangeLog
from app.dal.repositories.abstractions.interfaces import AbstractTenderChangeLogRepo


class TenderChangeLogRepo(AbstractTenderChangeLogRepo):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, log_entry: TenderStatusChangeLog) -> TenderStatusChangeLog:
        self._session.add(log_entry)
        await self._session.flush()
        return log_entry

    async def get_list_with_total_by_tender_id(
            self,
            tender_id: UUID,
            limit: int,
            offset: int
    ) -> tuple[list[TenderStatusChangeLog], int]:
        statement = (
            select(TenderStatusChangeLog, func.count().over().label("total"))
            .where(TenderStatusChangeLog.tender_id == tender_id)
            .order_by(TenderStatusChangeLog.changed_at.desc(), TenderStatusChangeLog.id.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(statement)
        rows = result.all()
        if rows:
            return [row[0] for row in rows], rows[0][1]

        return [], await self._count_by_tender_id(tender_id)

    async def _count_by_tender_id(self, tender_id: UUID) -> int:
        statement = (
            select(func.count())
            .select_from(TenderStatusChangeLog)
            .where(TenderStatusChangeLog.tender_id == tender_id)
        )
        result = await self._session.execute(statement)
        return result.scalar_one()

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dal.models.db_models import Tender
from app.dal.repositories.abstractions.interfaces import AbstractTenderRepo
from app.enums.tender_status import TenderStatus


class TenderRepo(AbstractTenderRepo):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, tender: Tender) -> Tender:
        self._session.add(tender)
        await self._session.flush()
        return tender

    async def get_by_id(self, tender_id: UUID) -> Tender | None:
        return await self._session.get(Tender, tender_id)

    async def get_by_id_for_update(self, tender_id: UUID) -> Tender | None:
        statement = (
            select(Tender)
            .where(Tender.id == tender_id)
            .with_for_update()
        )
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def update_status(self, tender: Tender, new_status: TenderStatus, updated_by: UUID) -> Tender:
        tender.status = new_status
        tender.updated_by = updated_by
        await self._session.flush()
        return tender

    async def get_list_with_total(
            self,
            status: TenderStatus | None,
            limit: int,
            offset: int
    ) -> tuple[list[Tender], int]:
        statement = select(Tender, func.count().over().label("total"))
        if status is not None:
            statement = statement.where(Tender.status == status)
        statement = (
            statement
            .order_by(Tender.created_at.desc(), Tender.id.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(statement)
        rows = result.all()
        if rows:
            return [row[0] for row in rows], rows[0][1]

        return [], await self._count(status)

    async def _count(self, status: TenderStatus | None) -> int:
        statement = select(func.count()).select_from(Tender)
        if status is not None:
            statement = statement.where(Tender.status == status)
        result = await self._session.execute(statement)
        return result.scalar_one()

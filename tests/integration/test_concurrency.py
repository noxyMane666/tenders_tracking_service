import asyncio
import uuid

from sqlalchemy import delete

from app.api.models.api_models import GetChangeLogListParamsDTO
from app.dal.db.database import DataBase
from app.dal.models.db_models import Tender, TenderStatusChangeLog
from app.dal.uow.sqlalchemy_uow import SqlAlchemyUnitOfWork
from app.enums.tender_status import TenderStatus
from app.exceptions.domain_exceptions import InvalidTenderStatusTransitionException
from app.services.tender_service import TenderServiceImpl
from tests.integration.conftest import make_create_dto, make_update_dto


async def test_concurrent_status_updates_on_the_same_tender_are_serialized(
        database: DataBase,
        user_id: uuid.UUID
) -> None:
    """Two real sessions race a status update on the same tender; exactly
    one should win the row lock, the other should see the new status
    and get rejected."""
    async with database.session_factory() as setup_session:
        setup_service = TenderServiceImpl(SqlAlchemyUnitOfWork(setup_session))
        tender = await setup_service.create_tender(make_create_dto(), user_id)
        tender = await setup_service.update_tender_status(tender.id, make_update_dto(TenderStatus.ACTIVE), user_id)

    try:
        async def attempt(new_status: TenderStatus) -> TenderStatus | Exception:
            async with database.session_factory() as session:
                service = TenderServiceImpl(SqlAlchemyUnitOfWork(session))
                try:
                    updated = await service.update_tender_status(
                        tender.id, make_update_dto(new_status), user_id
                    )
                    return updated.status
                except InvalidTenderStatusTransitionException as e:
                    return e

        results = await asyncio.gather(
            attempt(TenderStatus.WON),
            attempt(TenderStatus.LOST),
        )

        successes = [r for r in results if isinstance(r, TenderStatus)]
        failures = [r for r in results if isinstance(r, InvalidTenderStatusTransitionException)]

        assert len(successes) == 1, f"expected exactly one winner, got {results}"
        assert len(failures) == 1, f"expected exactly one rejection, got {results}"
        assert successes[0] in (TenderStatus.WON, TenderStatus.LOST)

        async with database.session_factory() as verify_session:
            verify_service = TenderServiceImpl(SqlAlchemyUnitOfWork(verify_session))
            final = await verify_service.get_tender_by_id(tender.id)
            assert final.status == successes[0]

            history = await verify_service.get_tender_history(tender.id, GetChangeLogListParamsDTO(limit=10))
            assert history.total == 2
            assert history.items[0].new_status == successes[0]
    finally:
        async with database.session_factory() as cleanup_session:
            await cleanup_session.execute(
                delete(TenderStatusChangeLog).where(TenderStatusChangeLog.tender_id == tender.id)
            )
            await cleanup_session.execute(delete(Tender).where(Tender.id == tender.id))
            await cleanup_session.commit()

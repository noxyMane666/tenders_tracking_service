import logging
from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession

from app.dal.repositories.tender_change_log_repo import TenderChangeLogRepo
from app.dal.repositories.tender_repo import TenderRepo
from app.dal.uow.abstractions.interfaces import AbstractUnitOfWork


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session: AsyncSession):
        self._session = session
        self.tenders = TenderRepo(session)
        self.change_logs = TenderChangeLogRepo(session)
        self._logger = logging.getLogger(__name__)
        self._read_only = False

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        self._read_only = False
        return self

    def mark_read_only(self) -> None:
        self._read_only = True

    async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None
    ) -> None:
        if exc_type is not None:
            self._logger.debug(
                "Rolling back transaction due to exception",
                extra={"event": "uow_rollback", "exception_type": exc_type.__name__},
            )
            await self.rollback()
            return

        if self._read_only:
            await self.rollback()
            self._logger.debug(
                "Transaction rolled back (read-only)",
                extra={"event": "uow_readonly_rollback"},
            )
            return

        try:
            await self.commit()
        except Exception:
            self._logger.exception(
                "Transaction commit failed, rolling back",
                extra={"event": "uow_commit_failed"},
            )
            await self.rollback()
            raise
        else:
            self._logger.debug("Transaction committed", extra={"event": "uow_commit"})

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

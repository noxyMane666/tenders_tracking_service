from abc import ABC, abstractmethod
from types import TracebackType

from app.dal.repositories.abstractions.interfaces import (
    AbstractTenderChangeLogRepo,
    AbstractTenderRepo
)


class AbstractUnitOfWork(ABC):
    """Transaction boundary around the repositories: commits on a clean
    `async with` exit, rolls back on exception."""

    tenders: AbstractTenderRepo
    change_logs: AbstractTenderChangeLogRepo

    @abstractmethod
    async def __aenter__(self) -> "AbstractUnitOfWork":
        pass

    @abstractmethod
    async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None
    ) -> None:
        pass

    @abstractmethod
    async def commit(self) -> None:
        pass

    @abstractmethod
    async def rollback(self) -> None:
        pass

    @abstractmethod
    def mark_read_only(self) -> None:
        """Roll back instead of commit on exit, even without an exception."""

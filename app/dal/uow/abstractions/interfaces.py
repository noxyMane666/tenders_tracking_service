from abc import ABC, abstractmethod
from types import TracebackType

from app.dal.repositories.abstractions.interfaces import (
    AbstractTenderChangeLogRepo,
    AbstractTenderRepo
)


class AbstractUnitOfWork(ABC):
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

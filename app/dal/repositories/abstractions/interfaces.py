from abc import ABC, abstractmethod
from uuid import UUID

from app.dal.models.db_models import Tender, TenderStatusChangeLog
from app.enums.tender_status import TenderStatus


class AbstractTenderRepo(ABC):
    @abstractmethod
    async def add(self, tender: Tender) -> Tender:
        pass

    @abstractmethod
    async def get_by_id(self, tender_id: UUID) -> Tender | None:
        pass

    @abstractmethod
    async def get_by_id_for_update(self, tender_id: UUID) -> Tender | None:
        pass

    @abstractmethod
    async def update_status(self, tender: Tender, new_status: TenderStatus, updated_by: UUID) -> Tender:
        pass

    @abstractmethod
    async def get_list(
            self,
            status: TenderStatus | None,
            limit: int,
            offset: int
    ) -> list[Tender]:
        pass

    @abstractmethod
    async def count(self, status: TenderStatus | None) -> int:
        pass


class AbstractTenderChangeLogRepo(ABC):
    @abstractmethod
    async def add(self, log_entry: TenderStatusChangeLog) -> TenderStatusChangeLog:
        pass

    @abstractmethod
    async def get_list_by_tender_id(
            self,
            tender_id: UUID,
            limit: int,
            offset: int
    ) -> list[TenderStatusChangeLog]:
        pass

    @abstractmethod
    async def count_by_tender_id(self, tender_id: UUID) -> int:
        pass

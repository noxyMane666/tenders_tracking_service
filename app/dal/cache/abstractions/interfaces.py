from abc import ABC, abstractmethod
from uuid import UUID

from app.api.models.api_models import TenderResponseDTO


class AbstractTenderCache(ABC):
    """Best-effort cache for single-tender reads. Never a source of truth —
    a lookup miss or a backend failure must fall through to the database."""

    @abstractmethod
    async def get_tender(self, tender_id: UUID) -> TenderResponseDTO | None:
        pass

    @abstractmethod
    async def set_tender(self, tender: TenderResponseDTO) -> None:
        pass

    @abstractmethod
    async def invalidate_tender(self, tender_id: UUID) -> None:
        pass

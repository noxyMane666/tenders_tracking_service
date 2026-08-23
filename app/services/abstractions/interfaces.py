from abc import ABC, abstractmethod
from uuid import UUID

from app.api.models.api_models import CreateTenderDTO, TenderResponseDTO, UpdateTenderStatusDTO, GetTenderListParamsDTO, \
    TenderListResponseDTO, GetChangeLogListParamsDTO, ChangeLogListResponseDTO


class AbstractTenderService(ABC):
    @abstractmethod
    async def create_tender(
            self,
            create_tender_dto: CreateTenderDTO,
            current_user_id: UUID
    ) -> TenderResponseDTO:
        pass

    @abstractmethod
    async def update_tender_status(
            self,
            tender_id: UUID,
            update_tender_status_dto: UpdateTenderStatusDTO,
            current_user_id: UUID
    ) -> TenderResponseDTO:
        pass

    @abstractmethod
    async def get_tender_by_id(self, tender_id: UUID) -> TenderResponseDTO:
        pass

    @abstractmethod
    async def get_tenders(self, request_params: GetTenderListParamsDTO) -> TenderListResponseDTO:
        pass

    @abstractmethod
    async def get_tender_history(
            self,
            tender_id: UUID,
            request_params: GetChangeLogListParamsDTO
    ) -> ChangeLogListResponseDTO:
        pass


class AbstractAuthService(ABC):
    @abstractmethod
    def get_current_user_id(self, token: str) -> UUID:
        pass

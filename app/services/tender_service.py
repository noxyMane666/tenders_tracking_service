import logging
from uuid import UUID

from app.api.models.api_models import (
    ChangeLogListResponseDTO,
    CreateTenderDTO,
    GetChangeLogListParamsDTO,
    GetTenderListParamsDTO,
    TenderListResponseDTO,
    TenderResponseDTO,
    TenderStatusChangeResponseDTO,
    UpdateTenderStatusDTO
)
from app.dal.models.db_models import Tender, TenderStatusChangeLog
from app.dal.uow.abstractions.interfaces import AbstractUnitOfWork
from app.enums.tender_status import TenderStatus
from app.exceptions.domain_exceptions import (
    InvalidTenderStatusTransitionException,
    TenderNotFoundException
)
from app.services.abstractions.interfaces import AbstractTenderService


class TenderServiceImpl(AbstractTenderService):
    _ALLOWED_STATUS_TRANSITIONS: dict[TenderStatus, frozenset[TenderStatus]] = {
        TenderStatus.DRAFT: frozenset({TenderStatus.ACTIVE}),
        TenderStatus.ACTIVE: frozenset({TenderStatus.WON, TenderStatus.LOST}),
        TenderStatus.WON: frozenset(),
        TenderStatus.LOST: frozenset(),
    }

    def __init__(self, uow: AbstractUnitOfWork):
        self._uow = uow
        self._logger = logging.getLogger(__name__)

    async def create_tender(
            self,
            create_tender_dto: CreateTenderDTO,
            current_user_id: UUID
    ) -> TenderResponseDTO:
        self._logger.info(
            "Tender creation requested",
            extra={
                "event": "tender_creation_requested",
                "created_by": str(current_user_id),
                "issuer_name": create_tender_dto.issuer_name,
            },
        )

        tender = Tender(
            created_by=current_user_id,
            updated_by=current_user_id,
            title=create_tender_dto.title,
            description=create_tender_dto.description,
            issuer_name=create_tender_dto.issuer_name,
            budget=create_tender_dto.budget,
            currency=create_tender_dto.currency,
            published_at=create_tender_dto.published_at,
            deadline_at=create_tender_dto.deadline_at,
        )
        async with self._uow as uow:
            await uow.tenders.add(tender)

            self._logger.info(
                "Tender created",
                extra={"event": "tender_created", "tender_id": str(tender.id)},
            )
            return TenderResponseDTO.model_validate(tender)

    async def update_tender_status(
            self,
            tender_id: UUID,
            update_tender_status_dto: UpdateTenderStatusDTO,
            current_user_id: UUID
    ) -> TenderResponseDTO:
        self._logger.info(
            "Tender status change requested",
            extra={
                "event": "tender_status_change_requested",
                "tender_id": str(tender_id),
                "new_status": update_tender_status_dto.new_status,
                "changed_by": str(current_user_id),
            },
        )

        async with self._uow as uow:
            tender = await uow.tenders.get_by_id_for_update(tender_id)
            if tender is None:
                raise TenderNotFoundException(tender_id)

            current_status = tender.status
            new_status = update_tender_status_dto.new_status
            self._ensure_transition_allowed(current_status, new_status)

            await uow.tenders.update_status(tender, new_status, current_user_id)
            log_entry = TenderStatusChangeLog(
                tender_id=tender_id,
                old_status=current_status,
                new_status=new_status,
                update_reason=update_tender_status_dto.update_reason,
                changed_by=current_user_id,
            )
            await uow.change_logs.add(log_entry)

            self._logger.info(
                "Tender status changed",
                extra={
                    "event": "tender_status_changed",
                    "tender_id": str(tender_id),
                    "old_status": current_status,
                    "new_status": new_status,
                },
            )
            return TenderResponseDTO.model_validate(tender)

    async def get_tender_by_id(self, tender_id: UUID) -> TenderResponseDTO:
        self._logger.debug(
            "Tender lookup requested",
            extra={"event": "tender_lookup_requested", "tender_id": str(tender_id)},
        )

        async with self._uow as uow:
            uow.mark_read_only()

            tender = await uow.tenders.get_by_id(tender_id)
            if tender is None:
                raise TenderNotFoundException(tender_id)

            return TenderResponseDTO.model_validate(tender)

    async def get_tenders(self, request_params: GetTenderListParamsDTO) -> TenderListResponseDTO:
        self._logger.debug(
            "Tender list requested",
            extra={
                "event": "tender_list_requested",
                "status": request_params.status,
                "limit": request_params.limit,
                "offset": request_params.offset,
            },
        )

        async with self._uow as uow:
            uow.mark_read_only()

            items, total = await uow.tenders.get_list_with_total(
                status=request_params.status,
                limit=request_params.limit,
                offset=request_params.offset,
            )

            self._logger.debug(
                "Tender list returned",
                extra={"event": "tender_list_returned", "total": total, "returned": len(items)},
            )
            return TenderListResponseDTO(
                items=[TenderResponseDTO.model_validate(tender) for tender in items],
                total=total,
                limit=request_params.limit,
                offset=request_params.offset,
            )

    async def get_tender_history(
            self,
            tender_id: UUID,
            request_params: GetChangeLogListParamsDTO
    ) -> ChangeLogListResponseDTO:
        self._logger.debug(
            "Tender history requested",
            extra={"event": "tender_history_requested", "tender_id": str(tender_id)},
        )

        async with self._uow as uow:
            uow.mark_read_only()

            tender = await uow.tenders.get_by_id(tender_id)
            if tender is None:
                raise TenderNotFoundException(tender_id)

            items, total = await uow.change_logs.get_list_with_total_by_tender_id(
                tender_id=tender_id,
                limit=request_params.limit,
                offset=request_params.offset,
            )

            self._logger.debug(
                "Tender history returned",
                extra={"event": "tender_history_returned", "tender_id": str(tender_id), "total": total},
            )
            return ChangeLogListResponseDTO(
                items=[TenderStatusChangeResponseDTO.model_validate(log_entry) for log_entry in items],
                total=total,
                limit=request_params.limit,
                offset=request_params.offset,
            )

    @classmethod
    def _ensure_transition_allowed(
            cls,
            current_status: TenderStatus,
            new_status: TenderStatus
    ) -> None:
        if new_status not in cls._ALLOWED_STATUS_TRANSITIONS[current_status]:
            raise InvalidTenderStatusTransitionException(current_status, new_status)

from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends

from app.dependencies.app_dependecies import get_current_user_id, get_tender_service
from app.services.abstractions.interfaces import AbstractTenderService
from app.api.models.api_models import (
    CreateTenderDTO,
    TenderResponseDTO,
    UpdateTenderStatusDTO,
    TenderListResponseDTO,
    GetTenderListParamsDTO,
    ChangeLogListResponseDTO,
    GetChangeLogListParamsDTO
)

router = APIRouter(prefix="/api/v1/tenders")

@router.post("", response_model=TenderResponseDTO, status_code=201)
async def create_tender(
        create_tender_dto: CreateTenderDTO,
        current_user_id: UUID = Depends(get_current_user_id),
        service: AbstractTenderService = Depends(get_tender_service)
) -> TenderResponseDTO:
    return await service.create_tender(create_tender_dto, current_user_id)

@router.patch("/{tender_id}/status", response_model=TenderResponseDTO, status_code=200)
async def update_tender_status(
        tender_id: UUID,
        update_tender_status_dto: UpdateTenderStatusDTO,
        current_user_id: UUID = Depends(get_current_user_id),
        service: AbstractTenderService = Depends(get_tender_service)
) -> TenderResponseDTO:
    return await service.update_tender_status(tender_id, update_tender_status_dto, current_user_id)

@router.get("/{tender_id}", response_model=TenderResponseDTO, status_code=200)
async def get_tender_by_id(
        tender_id: UUID,
        service: AbstractTenderService = Depends(get_tender_service)
) -> TenderResponseDTO:
    return await service.get_tender_by_id(tender_id)

@router.get("", response_model=TenderListResponseDTO, status_code=200)
async def get_tenders(
        request_params: GetTenderListParamsDTO = Depends(),
        service: AbstractTenderService = Depends(get_tender_service)
) -> TenderListResponseDTO:
    return await service.get_tenders(request_params)

@router.get("/{tender_id}/changelog", response_model=ChangeLogListResponseDTO, status_code=200)
async def get_tender_history_by_id(
        tender_id: UUID,
        request_params: GetChangeLogListParamsDTO = Depends(),
        service: AbstractTenderService = Depends(get_tender_service)
) -> ChangeLogListResponseDTO:
    return await service.get_tender_history(tender_id, request_params)

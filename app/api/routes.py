from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends

from app.api.models.api_models import CreateTenderDTO, TenderResponseDTO, UpdateTenderStatusDTO, \
    TenderStatusChangeResponseDTO, TenderListResponseDTO, GetTenderListParamsDTO, ChangeLogListResponseDTO, \
    GetChangeLogListParamsDTO

router = APIRouter(prefix="/api/v1/tenders")

@router.post("", response_model=TenderResponseDTO, status_code=201)
async def create_tender(
        create_tender_dto: CreateTenderDTO
) -> TenderResponseDTO:
    return ""

@router.patch("/{tender_id}/status", response_model=TenderResponseDTO, status_code=200)
async def update_tender_status(
        tender_id: UUID,
        update_tender_status_dto: UpdateTenderStatusDTO
) -> TenderResponseDTO:
    return ""

@router.get("/{tender_id}", response_model=TenderResponseDTO, status_code=200)
async def get_tender_by_id(
        tender_id: UUID
) -> TenderResponseDTO:
    return ""

@router.get("", response_model=TenderListResponseDTO, status_code=200)
async def get_tenders(
        request_params: GetTenderListParamsDTO = Depends()
) -> TenderListResponseDTO:
    return ""

@router.get("/{tender_id}/changelog", response_model=TenderStatusChangeResponseDTO, status_code=200)
async def get_tender_history_by_id(
        tender_id: UUID,
        request_params: GetChangeLogListParamsDTO = Depends()
) -> TenderStatusChangeResponseDTO:
    return ""



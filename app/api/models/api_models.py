from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.enums.tender_status import TenderStatus


class CreateTenderDTO(BaseModel):
    title: str
    description: str | None = None
    issuer_name: str
    budget: Decimal
    currency: str
    published_at: datetime | None = None
    deadline_at: datetime | None = None

class UpdateTenderStatusDTO(BaseModel):
    new_status: TenderStatus

class GetTenderListParamsDTO(BaseModel):
    status: TenderStatus | None = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

class GetChangeLogListParamsDTO(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

class TenderResponseDTO(BaseModel):
    id: UUID
    status: TenderStatus
    created_by: UUID
    title: str
    description: str | None
    issuer_name: str
    budget: Decimal
    currency: str
    published_at: datetime | None
    deadline_at: datetime | None
    created_at: datetime
    updated_at: datetime

class TenderListResponseDTO(BaseModel):
    items: list[TenderResponseDTO]
    total: int
    limit: int
    offset: int

class TenderStatusChangeResponseDTO(BaseModel):
    id: UUID
    tender_id: UUID
    old_status: TenderStatus
    new_status: TenderStatus
    update_reason: str | None
    changed_by: UUID
    changed_at: datetime

class ChangeLogListResponseDTO(BaseModel):
    items: list[TenderStatusChangeResponseDTO]
    total: int
    limit: int
    offset: int

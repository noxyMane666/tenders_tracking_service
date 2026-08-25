from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.enums.tender_status import TenderStatus


class CreateTenderDTO(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    issuer_name: str = Field(min_length=1, max_length=255)
    budget: Decimal = Field(gt=0, max_digits=15, decimal_places=2)
    currency: str = Field(min_length=3, max_length=3)
    published_at: datetime | None = None
    deadline_at: datetime | None = None

    @field_validator("published_at", "deadline_at")
    @classmethod
    def _require_timezone_aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("must include a timezone offset, e.g. '2026-01-01T00:00:00+00:00'")
        return value

    @model_validator(mode="after")
    def _check_deadline_after_published(self) -> "CreateTenderDTO":
        if self.published_at is not None and self.deadline_at is not None:
            if self.deadline_at <= self.published_at:
                raise ValueError("deadline_at must be after published_at")
        return self

class UpdateTenderStatusDTO(BaseModel):
    new_status: TenderStatus
    update_reason: str = Field(min_length=1)

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
    updated_by: UUID
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
    update_reason: str
    changed_by: UUID
    changed_at: datetime

class ChangeLogListResponseDTO(BaseModel):
    items: list[TenderStatusChangeResponseDTO]
    total: int
    limit: int
    offset: int

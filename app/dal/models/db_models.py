import uuid
from datetime import datetime
from uuid import UUID
from decimal import Decimal

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import (
    UUID as SqlAlchemyUUID,
    String,
    Text,
    Numeric,
    Enum,
    DateTime,
    func,
    ForeignKey, Index
)

from app.enums.tender_status import TenderStatus


class Base(DeclarativeBase):
    pass

class Tender(Base):
    __tablename__ = "tenders"

    id: Mapped[UUID] = mapped_column(
        SqlAlchemyUUID(as_uuid = True),
        primary_key=True,
        default=uuid.uuid4
    )
    status: Mapped[TenderStatus] = mapped_column(
        Enum(TenderStatus, name="tender_status"),
        nullable=False,
        default=TenderStatus.DRAFT
    )
    created_by: Mapped[UUID] = mapped_column(
        SqlAlchemyUUID(as_uuid=True),
        nullable=False
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    issuer_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    budget: Mapped[Decimal] = mapped_column(
        Numeric(precision=15, scale=2),
        nullable=False
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    deadline_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    status_changes: Mapped[list["TenderStatusChangeLog"]] = relationship(
        back_populates="tender",
    )

    __table_args__ = (
        Index(
            "ix_tenders_created_by",
            "created_by", "created_at"
        ),
        Index(
            "ix_tenders_updated_at",
            "updated_at"
        )
    )

class TenderStatusChangeLog(Base):
    __tablename__ = "tender_status_change_log"

    id: Mapped[UUID] = mapped_column(
        SqlAlchemyUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    tender_id: Mapped[UUID] = mapped_column(
        SqlAlchemyUUID(as_uuid=True),
        ForeignKey("tenders.id"),
        nullable=False
    )
    old_status: Mapped[TenderStatus] = mapped_column(
        Enum(TenderStatus, name="tender_status"),
        nullable=False
    )
    new_status: Mapped[TenderStatus] = mapped_column(
        Enum(TenderStatus, name="tender_status"),
        nullable=False
    )
    update_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    changed_by: Mapped[UUID] = mapped_column(
        SqlAlchemyUUID(as_uuid=True),
        nullable=False
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    tender: Mapped["Tender"] = relationship(
        back_populates="status_changes"
    )

    __table_args__ = (
        Index(
            "ix_tender_status_tender_changed",
            "tender_id", "changed_at"
        ),
        Index(
            "ix_tender_status_changed_by",
            "changed_by", "changed_at"
        )
    )



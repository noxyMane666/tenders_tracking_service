import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models.api_models import GetChangeLogListParamsDTO, GetTenderListParamsDTO
from app.dal.uow.sqlalchemy_uow import SqlAlchemyUnitOfWork
from app.enums.tender_status import TenderStatus
from app.exceptions.domain_exceptions import (
    InvalidTenderStatusTransitionException,
    TenderNotFoundException
)
from app.services.tender_service import TenderServiceImpl
from tests.conftest import make_create_dto, make_update_dto


async def test_create_tender_sets_created_by_and_updated_by_from_current_user(
        service: TenderServiceImpl,
        user_id: uuid.UUID
) -> None:
    tender = await service.create_tender(make_create_dto(), user_id)

    assert tender.created_by == user_id
    assert tender.updated_by == user_id
    assert tender.status == TenderStatus.DRAFT


async def test_create_tender_preserves_all_input_fields(
        service: TenderServiceImpl,
        user_id: uuid.UUID
) -> None:
    published_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    deadline_at = datetime(2026, 2, 1, tzinfo=timezone.utc)
    dto = make_create_dto(
        title="Road repair contract",
        description="Repaving the M4 section",
        issuer_name="Ministry of Transport",
        budget=Decimal("1234567.89"),
        currency="USD",
        published_at=published_at,
        deadline_at=deadline_at,
    )

    tender = await service.create_tender(dto, user_id)

    assert tender.title == "Road repair contract"
    assert tender.description == "Repaving the M4 section"
    assert tender.issuer_name == "Ministry of Transport"
    assert tender.budget == Decimal("1234567.89")
    assert tender.currency == "USD"
    assert tender.published_at == published_at
    assert tender.deadline_at == deadline_at


async def test_create_tender_gets_real_server_generated_timestamps(
        service: TenderServiceImpl,
        user_id: uuid.UUID
) -> None:
    tender = await service.create_tender(make_create_dto(), user_id)

    assert isinstance(tender.created_at, datetime)
    assert tender.created_at.tzinfo is not None
    assert tender.created_at == tender.updated_at


@pytest.mark.parametrize(
    ("current_status", "new_status"),
    [
        (TenderStatus.DRAFT, TenderStatus.ACTIVE),
        (TenderStatus.ACTIVE, TenderStatus.WON),
        (TenderStatus.ACTIVE, TenderStatus.LOST),
    ],
)
async def test_update_tender_status_allows_valid_transitions(
        service: TenderServiceImpl,
        user_id: uuid.UUID,
        current_status: TenderStatus,
        new_status: TenderStatus,
) -> None:
    tender = await service.create_tender(make_create_dto(), user_id)
    if current_status != TenderStatus.DRAFT:
        tender = await service.update_tender_status(tender.id, make_update_dto(current_status), user_id)

    updated = await service.update_tender_status(tender.id, make_update_dto(new_status), user_id)

    assert updated.status == new_status


@pytest.mark.parametrize(
    ("current_status", "rejected_status"),
    [
        (TenderStatus.DRAFT, TenderStatus.WON),
        (TenderStatus.DRAFT, TenderStatus.LOST),
        (TenderStatus.WON, TenderStatus.ACTIVE),
        (TenderStatus.LOST, TenderStatus.ACTIVE),
        (TenderStatus.WON, TenderStatus.LOST),
    ],
)
async def test_update_tender_status_rejects_invalid_transitions(
        service: TenderServiceImpl,
        user_id: uuid.UUID,
        current_status: TenderStatus,
        rejected_status: TenderStatus,
) -> None:
    tender = await service.create_tender(make_create_dto(), user_id)
    path_to_current = {
        TenderStatus.DRAFT: [],
        TenderStatus.ACTIVE: [TenderStatus.ACTIVE],
        TenderStatus.WON: [TenderStatus.ACTIVE, TenderStatus.WON],
        TenderStatus.LOST: [TenderStatus.ACTIVE, TenderStatus.LOST],
    }[current_status]
    for step in path_to_current:
        tender = await service.update_tender_status(tender.id, make_update_dto(step), user_id)

    with pytest.raises(InvalidTenderStatusTransitionException):
        await service.update_tender_status(tender.id, make_update_dto(rejected_status), user_id)


async def test_update_tender_status_rolls_back_on_invalid_transition(
        service: TenderServiceImpl,
        user_id: uuid.UUID
) -> None:
    tender = await service.create_tender(make_create_dto(), user_id)

    with pytest.raises(InvalidTenderStatusTransitionException):
        await service.update_tender_status(tender.id, make_update_dto(TenderStatus.WON), user_id)

    unchanged = await service.get_tender_by_id(tender.id)
    assert unchanged.status == TenderStatus.DRAFT

    history = await service.get_tender_history(tender.id, GetChangeLogListParamsDTO())
    assert history.total == 0


async def test_update_tender_status_not_found_raises(service: TenderServiceImpl, user_id: uuid.UUID) -> None:
    with pytest.raises(TenderNotFoundException):
        await service.update_tender_status(uuid.uuid4(), make_update_dto(TenderStatus.ACTIVE), user_id)


async def test_update_tender_status_records_change_log(
        service: TenderServiceImpl,
        user_id: uuid.UUID
) -> None:
    tender = await service.create_tender(make_create_dto(), user_id)
    other_user_id = uuid.uuid4()

    updated = await service.update_tender_status(
        tender.id,
        make_update_dto(TenderStatus.ACTIVE, update_reason="publishing now"),
        other_user_id,
    )

    assert updated.updated_by == other_user_id
    assert updated.created_by == user_id

    history = await service.get_tender_history(tender.id, GetChangeLogListParamsDTO())
    assert history.total == 1
    assert history.items[0].old_status == TenderStatus.DRAFT
    assert history.items[0].new_status == TenderStatus.ACTIVE
    assert history.items[0].changed_by == other_user_id
    assert history.items[0].update_reason == "publishing now"


async def test_get_tender_history_returns_items_newest_first(
        service: TenderServiceImpl,
        session: AsyncSession,
        user_id: uuid.UUID
) -> None:
    tender = await service.create_tender(make_create_dto(), user_id)
    await service.update_tender_status(tender.id, make_update_dto(TenderStatus.ACTIVE, "step 1"), user_id)
    await service.update_tender_status(tender.id, make_update_dto(TenderStatus.WON, "step 2"), user_id)

    await session.execute(
        text("UPDATE tender_status_change_log SET changed_at = :ts WHERE update_reason = :reason"),
        [
            {"ts": datetime(2026, 1, 1, tzinfo=timezone.utc), "reason": "step 1"},
            {"ts": datetime(2026, 1, 2, tzinfo=timezone.utc), "reason": "step 2"},
        ],
    )

    history = await service.get_tender_history(tender.id, GetChangeLogListParamsDTO())

    assert [item.update_reason for item in history.items] == ["step 2", "step 1"]


async def test_get_tender_history_respects_pagination(
        service: TenderServiceImpl,
        user_id: uuid.UUID
) -> None:
    tender = await service.create_tender(make_create_dto(), user_id)
    await service.update_tender_status(tender.id, make_update_dto(TenderStatus.ACTIVE), user_id)
    await service.update_tender_status(tender.id, make_update_dto(TenderStatus.WON), user_id)

    page = await service.get_tender_history(tender.id, GetChangeLogListParamsDTO(limit=1, offset=0))

    assert page.total == 2
    assert len(page.items) == 1


async def test_get_tender_history_not_found_raises(service: TenderServiceImpl) -> None:
    with pytest.raises(TenderNotFoundException):
        await service.get_tender_history(uuid.uuid4(), GetChangeLogListParamsDTO())


async def test_get_tender_by_id_not_found_raises(service: TenderServiceImpl) -> None:
    with pytest.raises(TenderNotFoundException):
        await service.get_tender_by_id(uuid.uuid4())


async def test_get_tender_by_id_returns_tender(service: TenderServiceImpl, user_id: uuid.UUID) -> None:
    created = await service.create_tender(make_create_dto(title="Find me"), user_id)

    fetched = await service.get_tender_by_id(created.id)

    assert fetched.id == created.id
    assert fetched.title == "Find me"


async def test_get_tenders_without_filter_returns_all_statuses(
        service: TenderServiceImpl,
        user_id: uuid.UUID
) -> None:
    draft = await service.create_tender(make_create_dto(title="Still draft"), user_id)
    active = await service.create_tender(make_create_dto(title="Active one"), user_id)
    active = await service.update_tender_status(active.id, make_update_dto(TenderStatus.ACTIVE), user_id)

    result = await service.get_tenders(GetTenderListParamsDTO())

    ids = {item.id for item in result.items}
    assert {draft.id, active.id} <= ids
    assert result.total == 2


async def test_get_tenders_filters_by_status(service: TenderServiceImpl, user_id: uuid.UUID) -> None:
    draft = await service.create_tender(make_create_dto(title="Still draft"), user_id)
    active = await service.create_tender(make_create_dto(title="Active one"), user_id)
    await service.update_tender_status(active.id, make_update_dto(TenderStatus.ACTIVE), user_id)

    result = await service.get_tenders(GetTenderListParamsDTO(status=TenderStatus.ACTIVE))

    ids = {item.id for item in result.items}
    assert active.id in ids
    assert draft.id not in ids
    assert result.total == 1


async def test_get_tenders_respects_pagination(service: TenderServiceImpl, user_id: uuid.UUID) -> None:
    for i in range(3):
        await service.create_tender(make_create_dto(title=f"Tender {i}"), user_id)

    page = await service.get_tenders(GetTenderListParamsDTO(limit=2, offset=0))

    assert page.total == 3
    assert len(page.items) == 2


async def test_get_tenders_offset_beyond_total_returns_empty_with_correct_total(
        service: TenderServiceImpl,
        user_id: uuid.UUID
) -> None:
    await service.create_tender(make_create_dto(), user_id)

    page = await service.get_tenders(GetTenderListParamsDTO(limit=20, offset=999))

    assert page.items == []
    assert page.total == 1


async def test_get_tenders_offset_beyond_total_with_status_filter_returns_correct_total(
        service: TenderServiceImpl,
        user_id: uuid.UUID
) -> None:
    active = await service.create_tender(make_create_dto(), user_id)
    await service.update_tender_status(active.id, make_update_dto(TenderStatus.ACTIVE), user_id)

    page = await service.get_tenders(
        GetTenderListParamsDTO(status=TenderStatus.ACTIVE, limit=20, offset=999)
    )

    assert page.items == []
    assert page.total == 1


async def test_write_paths_commit_read_paths_roll_back(
        service: TenderServiceImpl,
        uow: SqlAlchemyUnitOfWork,
        user_id: uuid.UUID
) -> None:
    with (
        patch.object(uow, "commit", wraps=uow.commit) as commit_spy,
        patch.object(uow, "rollback", wraps=uow.rollback) as rollback_spy,
    ):
        tender = await service.create_tender(make_create_dto(), user_id)
        assert commit_spy.await_count == 1
        assert rollback_spy.await_count == 0

        await service.get_tender_by_id(tender.id)
        assert commit_spy.await_count == 1
        assert rollback_spy.await_count == 1

        await service.get_tenders(GetTenderListParamsDTO())
        assert commit_spy.await_count == 1
        assert rollback_spy.await_count == 2

        await service.update_tender_status(tender.id, make_update_dto(TenderStatus.ACTIVE), user_id)
        assert commit_spy.await_count == 2
        assert rollback_spy.await_count == 2

        await service.get_tender_history(tender.id, GetChangeLogListParamsDTO())
        assert commit_spy.await_count == 2
        assert rollback_spy.await_count == 3

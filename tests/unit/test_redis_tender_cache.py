import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from app.api.models.api_models import TenderResponseDTO
from app.dal.cache.redis_tender_cache import RedisTenderCache
from app.enums.tender_status import TenderStatus


def _make_tender_dto(tender_id: uuid.UUID) -> TenderResponseDTO:
    user_id = uuid.uuid4()
    return TenderResponseDTO(
        id=tender_id,
        status=TenderStatus.DRAFT,
        created_by=user_id,
        updated_by=user_id,
        title="Test tender",
        description=None,
        issuer_name="ACME",
        budget=Decimal("100.00"),
        currency="RUB",
        published_at=None,
        deadline_at=None,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


@pytest.fixture
def failing_client() -> AsyncMock:
    client = AsyncMock()
    client.get.side_effect = RedisConnectionError("connection refused")
    client.set.side_effect = RedisConnectionError("connection refused")
    client.delete.side_effect = RedisConnectionError("connection refused")
    return client


async def test_get_tender_returns_none_on_redis_error(failing_client: AsyncMock) -> None:
    cache = RedisTenderCache(failing_client, ttl_seconds=60)

    result = await cache.get_tender(uuid.uuid4())

    assert result is None


async def test_set_tender_swallows_redis_error(failing_client: AsyncMock) -> None:
    cache = RedisTenderCache(failing_client, ttl_seconds=60)
    tender = _make_tender_dto(uuid.uuid4())

    await cache.set_tender(tender)


async def test_invalidate_tender_swallows_redis_error(failing_client: AsyncMock) -> None:
    cache = RedisTenderCache(failing_client, ttl_seconds=60)

    await cache.invalidate_tender(uuid.uuid4())


async def test_get_tender_returns_none_on_miss() -> None:
    client = AsyncMock()
    client.get.return_value = None
    cache = RedisTenderCache(client, ttl_seconds=60)

    result = await cache.get_tender(uuid.uuid4())

    assert result is None


async def test_set_then_get_round_trips_through_the_client() -> None:
    client = AsyncMock()
    stored: dict[str, bytes] = {}

    async def fake_set(key: str, value: str, ex: int) -> None:
        stored[key] = value.encode()

    async def fake_get(key: str) -> bytes | None:
        return stored.get(key)

    client.set.side_effect = fake_set
    client.get.side_effect = fake_get

    cache = RedisTenderCache(client, ttl_seconds=60)
    tender_id = uuid.uuid4()
    tender = _make_tender_dto(tender_id)

    await cache.set_tender(tender)
    result = await cache.get_tender(tender_id)

    assert result == tender

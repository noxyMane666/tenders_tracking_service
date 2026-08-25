import logging
from uuid import UUID

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.api.models.api_models import TenderResponseDTO
from app.dal.cache.abstractions.interfaces import AbstractTenderCache


class RedisTenderCache(AbstractTenderCache):
    def __init__(self, client: Redis, ttl_seconds: int):
        self._client = client
        self._ttl_seconds = ttl_seconds
        self._logger = logging.getLogger(__name__)

    @staticmethod
    def _key(tender_id: UUID) -> str:
        return f"tender:{tender_id}"

    async def get_tender(self, tender_id: UUID) -> TenderResponseDTO | None:
        try:
            raw = await self._client.get(self._key(tender_id))
        except RedisError:
            self._logger.warning(
                "Cache read failed, falling back to the database",
                extra={"event": "cache_read_failed", "tender_id": str(tender_id)},
            )
            return None

        if raw is None:
            return None
        return TenderResponseDTO.model_validate_json(raw)

    async def set_tender(self, tender: TenderResponseDTO) -> None:
        try:
            await self._client.set(
                self._key(tender.id),
                tender.model_dump_json(),
                ex=self._ttl_seconds,
            )
        except RedisError:
            self._logger.warning(
                "Cache write failed",
                extra={"event": "cache_write_failed", "tender_id": str(tender.id)},
            )

    async def invalidate_tender(self, tender_id: UUID) -> None:
        try:
            await self._client.delete(self._key(tender_id))
        except RedisError:
            self._logger.warning(
                "Cache invalidation failed",
                extra={"event": "cache_invalidate_failed", "tender_id": str(tender_id)},
            )

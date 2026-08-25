import logging
from collections.abc import Awaitable, Callable
from contextlib import AsyncExitStack

from redis.asyncio import Redis

from app.cofigurations.config import Configuration
from app.dal.cache.abstractions.interfaces import AbstractTenderCache
from app.dal.cache.redis_tender_cache import RedisTenderCache
from app.dal.db.database import DataBase
from app.services.abstractions.interfaces import AbstractAuthService
from app.services.auth_service import JwtAuthService


class AppResources:
    """Owns every resource with a process-wide lifetime, built once at
    startup and torn down once at shutdown."""

    def __init__(
            self,
            database: DataBase,
            auth_service: AbstractAuthService,
            redis_client: Redis,
            tender_cache: AbstractTenderCache
    ):
        self.database = database
        self.auth_service = auth_service
        self.redis_client = redis_client
        self.tender_cache = tender_cache
        self._logger = logging.getLogger(__name__)

    @classmethod
    async def create(cls, configuration: Configuration) -> "AppResources":
        async with AsyncExitStack() as stack:
            database = DataBase(configuration.db_settings)
            stack.push_async_callback(database.close)
            await database.check_db_connection()

            auth_service = JwtAuthService(configuration.auth_settings)

            redis_client = Redis.from_url(configuration.cache_settings.REDIS_URL)
            stack.push_async_callback(redis_client.aclose)

            tender_cache = RedisTenderCache(redis_client, configuration.cache_settings.CACHE_TTL_SECONDS)

            stack.pop_all()

        return cls(
            database=database,
            auth_service=auth_service,
            redis_client=redis_client,
            tender_cache=tender_cache
        )

    def _closers(self) -> list[tuple[str, Callable[[], Awaitable[None]]]]:
        return [
            ("database", self.database.close),
            ("redis_client", self.redis_client.aclose),
        ]

    async def close(self) -> None:
        for name, closer in self._closers():
            try:
                await closer()
            except Exception:
                self._logger.exception(
                    f"Failed to close resource: {name}",
                    extra={"event": "resource_close_failed", "resource": name},
                )

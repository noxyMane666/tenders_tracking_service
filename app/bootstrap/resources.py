import logging
from collections.abc import Awaitable, Callable
from contextlib import AsyncExitStack

from app.cofigurations.config import Configuration
from app.dal.db.database import DataBase
from app.services.abstractions.interfaces import AbstractAuthService
from app.services.auth_service import JwtAuthService


class AppResources:
    def __init__(self, database: DataBase, auth_service: AbstractAuthService):
        self.database = database
        self.auth_service = auth_service
        self._logger = logging.getLogger(__name__)

    @classmethod
    async def create(cls, configuration: Configuration) -> "AppResources":
        async with AsyncExitStack() as stack:
            database = DataBase(configuration.db_settings)
            stack.push_async_callback(database.close)
            await database.check_db_connection()

            auth_service = JwtAuthService(configuration.auth_settings)

            stack.pop_all()
            return cls(database=database, auth_service=auth_service)

    def _closers(self) -> list[tuple[str, Callable[[], Awaitable[None]]]]:
        return [
            ("database", self.database.close),
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

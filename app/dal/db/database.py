import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker
)

from app.cofigurations.db_settings import DataBaseSettings


class DataBase:
    def __init__(self, settings: DataBaseSettings):
        self.engine: AsyncEngine = create_async_engine(
            url=settings.DB_CONNECTION_STRING,
            echo=settings.ECHO,
            pool_size=settings.MAX_POOL_SIZE,
            max_overflow=settings.MAX_OVERFLOW,
            pool_timeout=settings.POOL_TIMEOUT
        )
        self.session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        self._logger = logging.getLogger(__name__)

    async def check_db_connection(self) -> None:
        async with self.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        self._logger.info("Database connection verified", extra={"event": "db_connection_verified"})

    async def close(self) -> None:
        await self.engine.dispose()
        self._logger.info("Database engine disposed", extra={"event": "db_engine_disposed"})
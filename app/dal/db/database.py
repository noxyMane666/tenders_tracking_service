from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
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
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_= AsyncEngine,
            expire_on_commit=False
        )

    async def check_db_connection(self):
        async with self.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    async def close(self):
        await self.engine.dispose()
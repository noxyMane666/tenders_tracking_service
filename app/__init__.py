import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.cofigurations.config import Configuration
from app.cofigurations.logger_config import setup_logging
from app.dal.db.database import DataBase
from app.exceptions.exception_handler import register_exception_handlers
from app.services.auth_service import JwtAuthService

setup_logging()
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    configuration = Configuration()
    database = DataBase(configuration.db_settings)
    auth_service = JwtAuthService(configuration.auth_settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        logger.info("Application is started", extra={"event": "app_started"})

        try:
            await database.check_db_connection()
        except Exception:
            logger.exception(
                "Database is unreachable at startup",
                extra={"event": "db_unreachable_at_startup"},
            )
            raise

        yield

        await database.close()
        logger.info("Application is shut down", extra={"event": "app_shutdown"})

    app = FastAPI(lifespan=lifespan)
    app.state.database = database
    app.state.auth_service = auth_service
    app.include_router(router=router)
    register_exception_handlers(app, logger)
    return app

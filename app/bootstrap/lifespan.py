import logging
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from fastapi import FastAPI

from app.bootstrap.resources import AppResources
from app.cofigurations.config import Configuration

logger = logging.getLogger(__name__)


def build_lifespan(configuration: Configuration) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        logger.info("Application is started", extra={"event": "app_started"})

        try:
            resources = await AppResources.create(configuration)
        except Exception:
            logger.exception(
                "Failed to initialize application resources",
                extra={"event": "app_resources_init_failed"},
            )
            raise

        app.state.database = resources.database
        app.state.auth_service = resources.auth_service

        yield

        await resources.close()
        logger.info("Application is shut down", extra={"event": "app_shutdown"})

    return lifespan

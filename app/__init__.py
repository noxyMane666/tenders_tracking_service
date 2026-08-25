import logging

from fastapi import FastAPI

from app.api.routes import router
from app.bootstrap.lifespan import build_lifespan
from app.cofigurations.config import Configuration
from app.cofigurations.logger_config import setup_logging
from app.exceptions.exception_handler import register_exception_handlers
from app.middleware.logging_middleware import register_logging_middleware

setup_logging()
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    configuration = Configuration()

    app = FastAPI(lifespan=build_lifespan(configuration))
    app.include_router(router=router)
    register_logging_middleware(app, logger)
    register_exception_handlers(app, logger)
    return app

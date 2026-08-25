import logging
import time
import uuid

from fastapi import FastAPI, Request

from app.cofigurations.logger_config import clear_request_context, set_request_context


def register_logging_middleware(app: FastAPI, logger: logging.Logger) -> None:
    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        set_request_context(request_id, request.method, request.url.path)

        start_time = time.perf_counter()
        response = None
        try:
            response = await call_next(request)
            return response
        finally:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            status_code = response.status_code if response is not None else 500
            logger.info(
                "Request completed",
                extra={
                    "event": "request_completed",
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                },
            )
            if response is not None:
                response.headers["x-request-id"] = request_id
            clear_request_context()

import logging

from fastapi import FastAPI, Request
from starlette.responses import JSONResponse


def register_body_size_middleware(app: FastAPI, logger: logging.Logger, max_body_size: int) -> None:
    @app.middleware("http")
    async def limit_body_size(request: Request, call_next):
        content_length = request.headers.get("content-length")

        if content_length:
            try:
                declared_length = int(content_length)
            except ValueError:
                declared_length = None

            if declared_length and declared_length > max_body_size:
                logger.warning(
                    "Request body too large",
                    extra={"event": "request_body_too_large", "declared_size": declared_length, "max_bytes": max_body_size}
                )
                return JSONResponse(
                    status_code=413,
                    content={"message": f"Request body exceeds the {max_body_size} bytes limit"}
                )

        return await call_next(request)
import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.exceptions.domain_exceptions import (
    DomainException,
    InvalidAuthTokenException,
    InvalidTenderStatusTransitionException,
    TenderNotFoundException
)

_DOMAIN_EXCEPTION_STATUS_CODES: dict[type, int] = {
    TenderNotFoundException: 404,
    InvalidTenderStatusTransitionException: 409,
    InvalidAuthTokenException: 401,
}
_UNMAPPED_DOMAIN_EXCEPTION_STATUS_CODE = 500


def register_exception_handlers(app: FastAPI, logger: logging.Logger) -> None:
    handler = GlobalExceptionHandler(logger)
    app.add_exception_handler(HTTPException, handler.handle)
    app.add_exception_handler(RequestValidationError, handler.handle)
    app.add_exception_handler(DomainException, handler.handle)
    app.add_exception_handler(Exception, handler.handle)


class GlobalExceptionHandler:
    def __init__(self, logger: logging.Logger):
        self._logger = logger

    @staticmethod
    def _request_id_header(request: Request) -> dict[str, str]:
        request_id = getattr(request.state, "request_id", None)
        return {"x-request-id": request_id} if request_id else {}

    async def handle(self, request: Request, exc: Exception) -> JSONResponse:
        if isinstance(exc, HTTPException):
            return self._handle_http_exception(request, exc)
        if isinstance(exc, DomainException):
            return self._handle_domain_exception(request, exc)
        if isinstance(exc, RequestValidationError):
            return self._handle_validation_error(request, exc)
        return self._handle_unexpected_exception(request, exc)

    def _handle_http_exception(self, request: Request, exc: HTTPException) -> JSONResponse:
        self._logger.warning(
            "HTTP error",
            extra={"event": "http_error", "status_code": exc.status_code, "detail": exc.detail},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": exc.detail},
            headers=self._request_id_header(request),
        )

    def _handle_domain_exception(self, request: Request, exc: DomainException) -> JSONResponse:
        status_code = _DOMAIN_EXCEPTION_STATUS_CODES.get(type(exc), _UNMAPPED_DOMAIN_EXCEPTION_STATUS_CODE)
        log_extra = {
            "event": "domain_error",
            "exception_type": type(exc).__name__,
            "status_code": status_code,
            "detail": str(exc),
        }
        if status_code >= 500:
            self._logger.exception("Domain error", extra=log_extra)
            client_message = "Internal Server Error"
        else:
            self._logger.warning("Domain error", extra=log_extra)
            client_message = str(exc)

        return JSONResponse(
            status_code=status_code,
            content={"message": client_message},
            headers=self._request_id_header(request),
        )

    def _handle_validation_error(self, request: Request, exc: RequestValidationError) -> JSONResponse:
        details = jsonable_encoder(exc.errors())
        self._logger.warning(
            "Validation error",
            extra={"event": "validation_error", "details": details},
        )
        return JSONResponse(
            status_code=422,
            content={"message": "Validation error", "details": details},
            headers=self._request_id_header(request),
        )

    def _handle_unexpected_exception(self, request: Request, exc: Exception) -> JSONResponse:
        self._logger.exception("Unhandled exception", extra={"event": "unhandled_exception"})
        return JSONResponse(
            status_code=500,
            content={"message": "Internal Server Error"},
            headers=self._request_id_header(request),
        )

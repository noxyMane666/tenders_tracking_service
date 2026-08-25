import logging
import uuid
from collections.abc import AsyncIterator

import httpx
import pytest_asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.exceptions.domain_exceptions import DomainException, TenderNotFoundException
from app.exceptions.exception_handler import register_exception_handlers


class _UnmappedDomainException(DomainException):
    def __init__(self) -> None:
        super().__init__("internal detail: constraint xyz_fk violated on secret_internal_table")


class _Body(BaseModel):
    value: int


def _build_probe_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app, logging.getLogger("test-exception-handler"))

    @app.get("/mapped-404")
    async def mapped_404() -> None:
        raise TenderNotFoundException(uuid.uuid4())

    @app.get("/http-exception")
    async def http_exception() -> None:
        raise HTTPException(status_code=403, detail="forbidden by a plain HTTPException")

    @app.get("/unmapped-500")
    async def unmapped_500() -> None:
        raise _UnmappedDomainException()

    @app.get("/unhandled")
    async def unhandled() -> None:
        raise RuntimeError("raw unexpected exception, not a DomainException")

    @app.post("/validate")
    async def validate(body: _Body) -> _Body:
        return body

    return app


@pytest_asyncio.fixture
async def probe_client() -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=_build_probe_app(), raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def test_mapped_domain_exception_returns_its_own_status_and_message(
        probe_client: httpx.AsyncClient
) -> None:
    response = await probe_client.get("/mapped-404")

    assert response.status_code == 404
    assert "not found" in response.json()["message"]


async def test_plain_http_exception_returns_its_own_status_and_detail(
        probe_client: httpx.AsyncClient
) -> None:
    response = await probe_client.get("/http-exception")

    assert response.status_code == 403
    assert response.json()["message"] == "forbidden by a plain HTTPException"


async def test_unmapped_domain_exception_returns_generic_500_message(
        probe_client: httpx.AsyncClient
) -> None:
    response = await probe_client.get("/unmapped-500")

    assert response.status_code == 500
    body = response.json()
    assert body["message"] == "Internal Server Error"
    assert "secret_internal_table" not in body["message"]


async def test_unhandled_exception_returns_generic_500_message(probe_client: httpx.AsyncClient) -> None:
    response = await probe_client.get("/unhandled")

    assert response.status_code == 500
    assert response.json()["message"] == "Internal Server Error"


async def test_validation_error_returns_422_with_details(probe_client: httpx.AsyncClient) -> None:
    response = await probe_client.post("/validate", json={"value": "not-an-int"})

    assert response.status_code == 422
    body = response.json()
    assert body["message"] == "Validation error"
    assert body["details"]

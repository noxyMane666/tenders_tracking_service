import uuid
from typing import Any

from httpx import AsyncClient


def _tender_body(**overrides: Any) -> dict[str, Any]:
    defaults: dict[str, Any] = dict(
        title="Road repair contract",
        issuer_name="ACME",
        budget="500.00",
        currency="RUB",
    )
    defaults.update(overrides)
    return defaults


async def _create_tender(client: AsyncClient, auth_headers: dict[str, str], **overrides: Any) -> dict[str, Any]:
    response = await client.post("/api/v1/tenders", json=_tender_body(**overrides), headers=auth_headers)
    assert response.status_code == 201
    return response.json()


async def test_create_tender_requires_auth(client: AsyncClient) -> None:
    response = await client.post("/api/v1/tenders", json=_tender_body())

    assert response.status_code == 401


async def test_create_tender_returns_created_tender(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    response = await client.post("/api/v1/tenders", json=_tender_body(title="Road works"), headers=auth_headers)

    assert response.status_code == 201
    assert "x-request-id" in response.headers
    body = response.json()
    assert body["title"] == "Road works"
    assert body["status"] == "draft"


async def test_create_tender_rejects_invalid_body(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    response = await client.post(
        "/api/v1/tenders",
        json=_tender_body(currency="TOO-LONG"),
        headers=auth_headers,
    )

    assert response.status_code == 422
    assert response.json()["message"] == "Validation error"


async def test_get_tender_by_id_returns_created_tender(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    created = await _create_tender(client, auth_headers)

    response = await client.get(f"/api/v1/tenders/{created['id']}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


async def test_get_tender_by_id_not_found_returns_404(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    response = await client.get(f"/api/v1/tenders/{uuid.uuid4()}", headers=auth_headers)

    assert response.status_code == 404
    assert "x-request-id" in response.headers


async def test_get_tender_by_id_requires_auth(client: AsyncClient) -> None:
    response = await client.get(f"/api/v1/tenders/{uuid.uuid4()}")

    assert response.status_code == 401


async def test_list_tenders_includes_created_tender(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    created = await _create_tender(client, auth_headers)

    response = await client.get("/api/v1/tenders", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert any(item["id"] == created["id"] for item in body["items"])


async def test_list_tenders_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/tenders")

    assert response.status_code == 401


async def test_update_status_valid_transition_returns_updated_tender(
        client: AsyncClient,
        auth_headers: dict[str, str]
) -> None:
    created = await _create_tender(client, auth_headers)

    response = await client.patch(
        f"/api/v1/tenders/{created['id']}/status",
        json={"new_status": "active", "update_reason": "go live"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "active"


async def test_update_status_invalid_transition_returns_409(
        client: AsyncClient,
        auth_headers: dict[str, str]
) -> None:
    created = await _create_tender(client, auth_headers)

    response = await client.patch(
        f"/api/v1/tenders/{created['id']}/status",
        json={"new_status": "won", "update_reason": "skip ahead"},
        headers=auth_headers,
    )

    assert response.status_code == 409


async def test_update_status_missing_reason_returns_422(
        client: AsyncClient,
        auth_headers: dict[str, str]
) -> None:
    created = await _create_tender(client, auth_headers)

    response = await client.patch(
        f"/api/v1/tenders/{created['id']}/status",
        json={"new_status": "active"},
        headers=auth_headers,
    )

    assert response.status_code == 422


async def test_update_status_requires_auth(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    created = await _create_tender(client, auth_headers)

    response = await client.patch(
        f"/api/v1/tenders/{created['id']}/status",
        json={"new_status": "active", "update_reason": "go live"},
    )

    assert response.status_code == 401


async def test_get_changelog_reflects_status_update(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    created = await _create_tender(client, auth_headers)
    await client.patch(
        f"/api/v1/tenders/{created['id']}/status",
        json={"new_status": "active", "update_reason": "go live"},
        headers=auth_headers,
    )

    response = await client.get(f"/api/v1/tenders/{created['id']}/changelog", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["new_status"] == "active"
    assert body["items"][0]["update_reason"] == "go live"


async def test_get_changelog_requires_auth(client: AsyncClient) -> None:
    response = await client.get(f"/api/v1/tenders/{uuid.uuid4()}/changelog")

    assert response.status_code == 401


async def test_create_tender_with_oversized_body_returns_413(
        client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    response = await client.post(
        "/api/v1/tenders",
        json=_tender_body(description="x" * 40_000),
        headers=auth_headers,
    )

    assert response.status_code == 413
    assert "x-request-id" in response.headers

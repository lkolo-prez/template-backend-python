"""Integration tests for the widgets v1 API."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_create_and_get_widget(client: AsyncClient) -> None:
    create = await client.post(
        "/v1/widgets",
        json={"name": "Flux Capacitor", "quantity": 88},
    )
    assert create.status_code == 201
    created = create.json()
    assert created["name"] == "Flux Capacitor"
    assert created["quantity"] == 88
    widget_id = created["id"]

    fetched = await client.get(f"/v1/widgets/{widget_id}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == widget_id


async def test_list_widgets_pagination(client: AsyncClient) -> None:
    for i in range(3):
        await client.post("/v1/widgets", json={"name": f"w{i}"})

    page = await client.get("/v1/widgets", params={"limit": 2, "offset": 0})
    assert page.status_code == 200
    body = page.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2


async def test_update_widget(client: AsyncClient) -> None:
    created = (
        await client.post("/v1/widgets", json={"name": "Gizmo"})
    ).json()
    resp = await client.patch(
        f"/v1/widgets/{created['id']}", json={"quantity": 5}
    )
    assert resp.status_code == 200
    assert resp.json()["quantity"] == 5
    assert resp.json()["name"] == "Gizmo"


async def test_delete_widget(client: AsyncClient) -> None:
    created = (await client.post("/v1/widgets", json={"name": "Temp"})).json()
    delete = await client.delete(f"/v1/widgets/{created['id']}")
    assert delete.status_code == 204

    missing = await client.get(f"/v1/widgets/{created['id']}")
    assert missing.status_code == 404
    assert missing.headers["content-type"].startswith(
        "application/problem+json"
    )


async def test_get_unknown_widget_returns_problem_json(
    client: AsyncClient,
) -> None:
    import uuid

    resp = await client.get(f"/v1/widgets/{uuid.uuid4()}")
    assert resp.status_code == 404
    body = resp.json()
    assert body["title"] == "Not Found"
    assert body["status"] == 404


async def test_validation_error_returns_422(client: AsyncClient) -> None:
    resp = await client.post("/v1/widgets", json={"name": ""})
    assert resp.status_code == 422
    body = resp.json()
    assert body["title"] == "Unprocessable Entity"
    assert "errors" in body


async def test_extra_field_rejected(client: AsyncClient) -> None:
    resp = await client.post(
        "/v1/widgets", json={"name": "ok", "rogue": "field"}
    )
    assert resp.status_code == 422

"""Integration tests for the health endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_liveness(client: AsyncClient) -> None:
    resp = await client.get("/health/live")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "alive"
    assert body["service"]
    assert body["version"]


async def test_readiness(client: AsyncClient) -> None:
    resp = await client.get("/health/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"
    assert body["checks"]["self"] is True


async def test_security_headers_present(client: AsyncClient) -> None:
    resp = await client.get("/health/live")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'none'" in resp.headers["Content-Security-Policy"]


async def test_request_id_echoed(client: AsyncClient) -> None:
    resp = await client.get(
        "/health/live", headers={"X-Request-ID": "test-correlation-id"}
    )
    assert resp.headers["X-Request-ID"] == "test-correlation-id"


async def test_request_id_generated_when_absent(client: AsyncClient) -> None:
    resp = await client.get("/health/live")
    assert resp.headers.get("X-Request-ID")

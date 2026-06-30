"""Shared pytest fixtures.

Provides an isolated FastAPI application and an httpx ``AsyncClient`` bound to
it via ASGITransport, so integration tests exercise the real middleware stack
without binding a network socket.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.v1.widgets import WidgetRepository, get_repository
from app.config import Settings
from app.main import create_app


@pytest.fixture
def settings() -> Settings:
    """Return deterministic test settings (console logs, no OTel)."""
    return Settings(
        environment="local",
        log_json=False,
        otel_enabled=False,
    )


@pytest.fixture
def app(settings: Settings):
    """Construct a fresh app with an isolated in-memory widget repository."""
    application = create_app(settings)
    # Each test gets its own repository to avoid cross-test state leakage.
    repo = WidgetRepository()
    application.dependency_overrides[get_repository] = lambda: repo
    return application


@pytest_asyncio.fixture
async def client(app) -> AsyncIterator[AsyncClient]:
    """Yield an AsyncClient wired to the in-process ASGI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as ac:
        yield ac

"""Application factory and ASGI entrypoint.

``create_app`` wires together configuration, logging, telemetry, middleware,
exception handlers, and routers. The module-level ``app`` is the ASGI callable
used by uvicorn (``uvicorn app.main:app``).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.health import router as health_router
from app.api.v1 import api_router_v1
from app.config import Settings, get_settings
from app.exceptions import register_exception_handlers
from app.logging import configure_logging, get_logger
from app.middleware import RequestIdMiddleware, SecurityHeadersMiddleware
from app.telemetry import configure_telemetry

_log = get_logger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage startup/shutdown side effects."""
    settings: Settings = app.state.settings
    _log.info(
        "app.startup",
        service=settings.service_name,
        environment=settings.environment,
        version=__version__,
    )
    yield
    _log.info("app.shutdown")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Construct and configure the FastAPI application.

    Args:
        settings: Optional settings override (primarily for tests). Defaults to
            the cached process settings.

    Returns:
        A fully wired :class:`fastapi.FastAPI` instance.
    """
    settings = settings or get_settings()
    configure_logging(settings)

    app = FastAPI(
        title=settings.service_name,
        version=__version__,
        root_path=settings.root_path,
        # Hide interactive docs in production by default; expose via gateway if
        # needed. Adjust to your organisation's policy.
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
        openapi_url=None if settings.is_production else "/openapi.json",
        lifespan=_lifespan,
    )
    app.state.settings = settings

    # Middleware (order matters: last added runs outermost).
    app.add_middleware(SecurityHeadersMiddleware, enable_hsts=settings.is_production)
    app.add_middleware(RequestIdMiddleware)
    if settings.cors_allow_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_allow_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    register_exception_handlers(app)
    configure_telemetry(app, settings)

    app.include_router(health_router)
    app.include_router(api_router_v1)

    return app


# ASGI entrypoint used by uvicorn / the container CMD.
app = create_app()

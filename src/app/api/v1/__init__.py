"""Version 1 of the public HTTP API."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import widgets

api_router_v1 = APIRouter(prefix="/v1")
api_router_v1.include_router(widgets.router)

__all__ = ["api_router_v1"]

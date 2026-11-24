"""Health probe endpoints.

Two distinct probes following Kubernetes conventions:

* ``/health/live``  - liveness: is the process up and able to serve? Always
  cheap; never depends on downstream systems.
* ``/health/ready`` - readiness: is the service ready to receive traffic? This
  is where dependency checks (DB, cache, upstream APIs) belong.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Response, status
from pydantic import BaseModel

from app import __version__
from app.config import get_settings

router = APIRouter(prefix="/health", tags=["health"])


class LivenessResponse(BaseModel):
    """Liveness probe payload."""

    status: Literal["alive"] = "alive"
    service: str
    version: str


class ReadinessResponse(BaseModel):
    """Readiness probe payload."""

    status: Literal["ready", "not_ready"]
    checks: dict[str, bool]


@router.get(
    "/live",
    response_model=LivenessResponse,
    summary="Liveness probe",
)
async def live() -> LivenessResponse:
    """Return liveness status. Used by orchestrators to restart dead pods."""
    settings = get_settings()
    return LivenessResponse(service=settings.service_name, version=__version__)


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe",
)
async def ready(response: Response) -> ReadinessResponse:
    """Return readiness status.

    Extend ``checks`` with real dependency probes (database connectivity, cache
    reachability, upstream health). When any check fails, return 503 so traffic
    is not routed to this instance.
    """
    checks: dict[str, bool] = {
        # Replace with real dependency checks, e.g. "database": await db_ping().
        "self": True,
    }
    all_ok = all(checks.values())
    if not all_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(
        status="ready" if all_ok else "not_ready",
        checks=checks,
    )

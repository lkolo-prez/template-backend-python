"""Domain exceptions and FastAPI exception handlers.

Errors are returned as RFC 9457 (problem+json) style payloads so clients get a
consistent, machine-readable error contract. Internal errors never leak stack
traces or messages to the caller; they are logged server-side instead.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.logging import get_logger

_log = get_logger(__name__)

PROBLEM_CONTENT_TYPE = "application/problem+json"


class AppError(Exception):
    """Base class for expected, domain-level application errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    title: str = "Internal Server Error"

    def __init__(self, detail: str | None = None) -> None:
        """Create the error with an optional client-facing detail message."""
        self.detail = detail or self.title
        super().__init__(self.detail)


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""

    status_code = status.HTTP_404_NOT_FOUND
    title = "Not Found"


class ConflictError(AppError):
    """Raised when a resource already exists or violates a uniqueness rule."""

    status_code = status.HTTP_409_CONFLICT
    title = "Conflict"


def _problem(
    *,
    status_code: int,
    title: str,
    detail: str,
    request: Request,
    extra: dict[str, Any] | None = None,
) -> JSONResponse:
    """Build a problem+json response body."""
    body: dict[str, Any] = {
        "type": "about:blank",
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": str(request.url.path),
    }
    if extra:
        body.update(extra)
    return JSONResponse(
        status_code=status_code,
        content=body,
        media_type=PROBLEM_CONTENT_TYPE,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all application exception handlers on ``app``."""

    @app.exception_handler(AppError)
    async def _handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        _log.info(
            "request.domain_error",
            error_type=type(exc).__name__,
            status_code=exc.status_code,
        )
        return _problem(
            status_code=exc.status_code,
            title=exc.title,
            detail=exc.detail,
            request=request,
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _problem(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            title="Unprocessable Entity",
            detail="Request validation failed.",
            request=request,
            extra={"errors": exc.errors()},
        )

    @app.exception_handler(StarletteHTTPException)
    async def _handle_http_exception(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return _problem(
            status_code=exc.status_code,
            title=str(exc.detail),
            detail=str(exc.detail),
            request=request,
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        # Log the full exception server-side; never return details to clients.
        _log.error("request.unhandled_error", exc_info=exc)
        return _problem(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            title="Internal Server Error",
            detail="An unexpected error occurred.",
            request=request,
        )

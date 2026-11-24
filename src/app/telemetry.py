"""OpenTelemetry tracing setup.

Tracing is opt-in via ``APP_OTEL_ENABLED``. When enabled, spans are exported to
the configured OTLP endpoint and FastAPI/httpx are auto-instrumented. The setup
is intentionally defensive: a misconfigured collector must never crash the app.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.config import Settings
from app.logging import get_logger

if TYPE_CHECKING:
    from fastapi import FastAPI

_log = get_logger(__name__)


def configure_telemetry(app: FastAPI, settings: Settings) -> None:
    """Configure OpenTelemetry tracing for the application.

    Args:
        app: The FastAPI application instance to instrument.
        settings: Validated application settings.
    """
    if not settings.otel_enabled:
        _log.debug("telemetry.disabled")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:  # pragma: no cover - optional dependency guard
        _log.warning("telemetry.dependencies_missing")
        return

    resource = Resource.create(
        {
            "service.name": settings.service_name,
            "deployment.environment": settings.environment,
        }
    )
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    # excluded_urls keeps liveness/readiness probes out of the trace stream.
    FastAPIInstrumentor.instrument_app(app, excluded_urls="health/live,health/ready")
    HTTPXClientInstrumentor().instrument()

    _log.info(
        "telemetry.enabled",
        endpoint=settings.otel_exporter_otlp_endpoint,
    )

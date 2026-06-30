"""aircloud backend Python microservice template.

A production-grade FastAPI HTTP microservice template with structured logging,
OpenTelemetry instrumentation, typed configuration, and a hardened container
image.
"""

from __future__ import annotations

__all__ = ["__version__"]

# Single source of truth for the application version.
# release-please keeps this in sync via the Conventional Commits release flow.
__version__ = "0.1.0"

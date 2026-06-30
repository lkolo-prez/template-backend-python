"""Application configuration via pydantic-settings.

All settings are read from environment variables (optionally a local ``.env``
file during development). Settings are validated once at startup and exposed
through a cached :func:`get_settings` accessor so the rest of the codebase can
depend on a single, immutable configuration object.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "dev", "staging", "production"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """Strongly typed application settings.

    Environment variables are prefixed with ``APP_`` and are case-insensitive,
    e.g. ``APP_ENVIRONMENT=production`` populates :attr:`environment`.
    """

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )

    # Service identity ----------------------------------------------------
    service_name: str = Field(
        default="template-backend-python",
        description="Logical service name, used in logs and traces.",
    )
    environment: Environment = Field(
        default="local",
        description="Deployment environment.",
    )

    # HTTP server ---------------------------------------------------------
    host: str = Field(default="0.0.0.0", description="Bind address.")  # noqa: S104
    port: int = Field(default=8000, ge=1, le=65535, description="Bind port.")
    root_path: str = Field(
        default="",
        description="ASGI root_path when served behind a path-prefixing proxy.",
    )

    # Observability -------------------------------------------------------
    log_level: LogLevel = Field(default="INFO", description="Root log level.")
    log_json: bool = Field(
        default=True,
        description="Emit JSON logs (True) or console-friendly logs (False).",
    )
    otel_enabled: bool = Field(
        default=False,
        description="Enable OpenTelemetry tracing export.",
    )
    otel_exporter_otlp_endpoint: str | None = Field(
        default=None,
        description="OTLP gRPC/HTTP endpoint, e.g. http://collector:4317.",
    )

    # Behaviour -----------------------------------------------------------
    request_timeout_seconds: float = Field(
        default=10.0,
        gt=0,
        description="Default timeout for outbound httpx requests.",
    )
    cors_allow_origins: list[str] = Field(
        default_factory=list,
        description="Allowed CORS origins. Empty means CORS is disabled.",
    )

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        """Allow a comma-separated string for ``APP_CORS_ALLOW_ORIGINS``."""
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def is_production(self) -> bool:
        """Return ``True`` when running in the production environment."""
        return self.environment == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide cached settings instance."""
    return Settings()

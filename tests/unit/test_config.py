"""Unit tests for application configuration."""

from __future__ import annotations

import pytest

from app.config import Settings


def test_defaults() -> None:
    settings = Settings()
    assert settings.service_name == "template-backend-python"
    assert settings.environment == "local"
    assert settings.port == 8000
    assert settings.is_production is False


def test_is_production() -> None:
    assert Settings(environment="production").is_production is True


def test_cors_origins_from_csv_string() -> None:
    settings = Settings(cors_allow_origins="https://a.example, https://b.example")
    assert settings.cors_allow_origins == [
        "https://a.example",
        "https://b.example",
    ]


@pytest.mark.parametrize("port", [0, 70000])
def test_invalid_port_rejected(port: int) -> None:
    with pytest.raises(ValueError):  # noqa: PT011 - pydantic raises ValidationError
        Settings(port=port)


def test_env_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENVIRONMENT", "staging")
    monkeypatch.setenv("APP_PORT", "9090")
    settings = Settings()
    assert settings.environment == "staging"
    assert settings.port == 9090

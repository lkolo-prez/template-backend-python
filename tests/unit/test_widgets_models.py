"""Unit tests for widget Pydantic models and the in-memory repository."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.api.v1.widgets import WidgetCreate, WidgetRepository, WidgetUpdate
from app.exceptions import NotFoundError


def test_widget_create_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        WidgetCreate(name="ok", unexpected="nope")  # type: ignore[call-arg]


def test_widget_create_rejects_blank_name() -> None:
    with pytest.raises(ValidationError):
        WidgetCreate(name="")


def test_repository_crud_roundtrip() -> None:
    repo = WidgetRepository()
    created = repo.create(WidgetCreate(name="Gadget", quantity=3))

    assert repo.get(created.id) == created

    updated = repo.update(created.id, WidgetUpdate(quantity=10))
    assert updated.quantity == 10
    assert updated.name == "Gadget"  # unchanged field preserved
    assert updated.updated_at >= created.updated_at

    repo.delete(created.id)
    with pytest.raises(NotFoundError):
        repo.get(created.id)


def test_repository_get_missing_raises() -> None:
    repo = WidgetRepository()
    import uuid

    with pytest.raises(NotFoundError):
        repo.get(uuid.uuid4())

"""Widgets resource — an illustrative CRUD-style API surface.

This module is a worked example showing the patterns the template encourages:
Pydantic v2 request/response models, an in-memory repository abstraction behind
a dependency, typed path/query parameters, and domain exceptions translated to
problem+json responses.

Replace the in-memory ``WidgetRepository`` with a real persistence layer.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict, Field

from app.exceptions import NotFoundError

router = APIRouter(prefix="/widgets", tags=["widgets"])


# --------------------------------------------------------------------------- #
# Models                                                                       #
# --------------------------------------------------------------------------- #
class WidgetBase(BaseModel):
    """Fields shared by widget create/read models."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120, examples=["Flux Capacitor"])
    description: str | None = Field(
        default=None, max_length=2000, examples=["Makes time travel possible."]
    )
    quantity: int = Field(default=0, ge=0, le=1_000_000, examples=[42])


class WidgetCreate(WidgetBase):
    """Payload to create a widget."""


class WidgetUpdate(BaseModel):
    """Payload to partially update a widget."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    quantity: int | None = Field(default=None, ge=0, le=1_000_000)


class Widget(WidgetBase):
    """A persisted widget returned to clients."""

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class WidgetPage(BaseModel):
    """A page of widgets."""

    items: list[Widget]
    total: int


# --------------------------------------------------------------------------- #
# Repository (swap for a real datastore)                                       #
# --------------------------------------------------------------------------- #
class WidgetRepository:
    """In-memory widget store. Not safe for multi-process deployments."""

    def __init__(self) -> None:
        """Create an empty store."""
        self._store: dict[uuid.UUID, Widget] = {}

    def list(self, *, limit: int, offset: int) -> tuple[list[Widget], int]:
        """Return one page of widgets (oldest first) and the total count."""
        items = sorted(self._store.values(), key=lambda w: w.created_at)
        return items[offset : offset + limit], len(items)

    def get(self, widget_id: uuid.UUID) -> Widget:
        """Return a widget or raise ``NotFoundError``."""
        try:
            return self._store[widget_id]
        except KeyError as exc:
            raise NotFoundError(f"Widget {widget_id} not found.") from exc

    def create(self, data: WidgetCreate) -> Widget:
        """Persist a new widget and return it."""
        now = datetime.now(UTC)
        widget = Widget(
            id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
            **data.model_dump(),
        )
        self._store[widget.id] = widget
        return widget

    def update(self, widget_id: uuid.UUID, data: WidgetUpdate) -> Widget:
        """Apply a partial update to an existing widget and return it."""
        current = self.get(widget_id)
        patch = data.model_dump(exclude_unset=True)
        updated = current.model_copy(update={**patch, "updated_at": datetime.now(UTC)})
        self._store[widget_id] = updated
        return updated

    def delete(self, widget_id: uuid.UUID) -> None:
        """Remove a widget or raise ``NotFoundError``."""
        if widget_id not in self._store:
            raise NotFoundError(f"Widget {widget_id} not found.")
        del self._store[widget_id]


# Process-wide singleton repository. Overridden in tests via dependency_overrides.
_repository = WidgetRepository()


def get_repository() -> WidgetRepository:
    """FastAPI dependency returning the widget repository."""
    return _repository


RepositoryDep = Annotated[WidgetRepository, Depends(get_repository)]


# --------------------------------------------------------------------------- #
# Routes                                                                       #
# --------------------------------------------------------------------------- #
@router.get("", response_model=WidgetPage, summary="List widgets")
async def list_widgets(
    repo: RepositoryDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> WidgetPage:
    """Return a page of widgets ordered by creation time."""
    items, total = repo.list(limit=limit, offset=offset)
    return WidgetPage(items=items, total=total)


@router.post(
    "",
    response_model=Widget,
    status_code=status.HTTP_201_CREATED,
    summary="Create a widget",
)
async def create_widget(payload: WidgetCreate, repo: RepositoryDep) -> Widget:
    """Create a new widget and return the persisted representation."""
    return repo.create(payload)


@router.get("/{widget_id}", response_model=Widget, summary="Get a widget")
async def get_widget(widget_id: uuid.UUID, repo: RepositoryDep) -> Widget:
    """Return a single widget by ID, or 404 if it does not exist."""
    return repo.get(widget_id)


@router.patch("/{widget_id}", response_model=Widget, summary="Update a widget")
async def update_widget(
    widget_id: uuid.UUID, payload: WidgetUpdate, repo: RepositoryDep
) -> Widget:
    """Partially update an existing widget."""
    return repo.update(widget_id, payload)


@router.delete(
    "/{widget_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a widget",
)
async def delete_widget(widget_id: uuid.UUID, repo: RepositoryDep) -> None:
    """Delete a widget by ID."""
    repo.delete(widget_id)

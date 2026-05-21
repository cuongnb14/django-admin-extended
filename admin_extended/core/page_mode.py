"""Page mode (view / edit / add) for the admin changeform.

Implemented via ``contextvars.ContextVar`` so the request object is never
mutated. ``ExtendedModelAdmin._changeform_view`` enters ``page_mode_scope``
at the start of every request and exits it in a ``finally`` block.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from enum import StrEnum
from typing import Iterator

from django.http import HttpRequest


class PageMode(StrEnum):
    VIEW = "view"
    EDIT = "edit"
    ADD = "add"


_page_mode_var: ContextVar[PageMode | None] = ContextVar("admin_extended_page_mode", default=None)


def current_page_mode() -> PageMode | None:
    """Return the page mode set by the active ``page_mode_scope``, or None."""
    return _page_mode_var.get()


@contextmanager
def page_mode_scope(mode: PageMode) -> Iterator[None]:
    """Set the page mode for the duration of the with-block."""
    token = _page_mode_var.set(mode)
    try:
        yield
    finally:
        _page_mode_var.reset(token)


def get_page_mode(request: HttpRequest, object_id: str | int | None) -> PageMode:
    """Classify the page mode from request + object_id.

    ADD when no object_id; EDIT when ``?edit=`` or ``?_popup=`` present; VIEW otherwise.
    """
    if object_id is None:
        return PageMode.ADD
    if "edit" in request.GET or "_popup" in request.GET:
        return PageMode.EDIT
    return PageMode.VIEW

"""Fieldset filtering helpers used by ExtendedModelAdmin.

These are pure functions — they do not depend on a request or admin
instance. ExtendedModelAdmin composes them into ``get_fieldsets``.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

Fieldset = tuple[str | None, dict[str, Any]]


def is_display_only(field_name: str, read_only_fields: Iterable[str]) -> bool:
    """A field is display-only if explicitly listed or its name starts with 'display_'."""
    return field_name in read_only_fields or field_name.startswith("display_")


def filter_fieldsets(
    fieldsets: list[Fieldset] | tuple[Fieldset, ...],
    drop: Callable[[str], bool],
) -> list[Fieldset]:
    """Return a copy of ``fieldsets`` with any field for which ``drop(field)`` is True removed.

    Field entries may be strings or nested tuples/lists. Empty nested groups are dropped.
    The input is not mutated.
    """
    out: list[Fieldset] = []
    for name, opts in fieldsets:
        new_fields: list[Any] = []
        for entry in opts["fields"]:
            if isinstance(entry, str):
                if not drop(entry):
                    new_fields.append(entry)
            else:
                kept = tuple(item for item in entry if not drop(item))
                if kept:
                    new_fields.append(kept)
        new_opts = dict(opts)
        new_opts["fields"] = tuple(new_fields)
        out.append((name, new_opts))
    return out

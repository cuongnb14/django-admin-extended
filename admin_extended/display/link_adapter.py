"""Adapter that converts FK fields in list_display to clickable links."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from django.contrib import admin
from django.db.models import ForeignKey
from django.urls import reverse
from django.utils.html import format_html


class DisplayLinkAdapter:
    """Mixin for ModelAdmin that turns FK columns into change-page links.

    Skip rules (NOT converted to links):
      * field already in ``list_display_links``
      * entry is callable
      * field is not a ForeignKey
      * ``enable_foreign_link`` is False
    """

    enable_foreign_link: bool = True

    def _foreign_key_link(self, field_name: str, verbose_name: str) -> Callable[[Any], Any]:
        def display_fn(obj: Any) -> Any:
            linked = getattr(obj, field_name)
            if linked is None:
                return "-"
            app_label = linked._meta.app_label
            model_name = linked._meta.model_name
            url = reverse(f"admin:{app_label}_{model_name}_change", args=[linked.pk])
            return format_html('<a href="{}">{}</a>', url, linked)

        display_fn.short_description = verbose_name  # type: ignore[attr-defined]
        return display_fn

    def _fk_field_map(self) -> dict[str, str]:
        """Return a map of {fk_field_name: verbose_name} for the admin's model.

        Both the actual field name (``customer``) and the attname (``customer_id``)
        map to the same entry so consumers can write either in list_display.
        """
        out: dict[str, str] = {}
        for field in self.model._meta.fields:  # type: ignore[attr-defined]
            if isinstance(field, ForeignKey):
                out[field.name] = str(field.verbose_name)
                out[field.attname] = str(field.verbose_name)
        return out

    def _should_link(self, entry: Any, fk_map: dict[str, str], list_display_links: tuple[str, ...]) -> bool:
        if not self.enable_foreign_link:
            return False
        if not isinstance(entry, str):
            return False
        if entry in list_display_links:
            return False
        return entry in fk_map

    def get_list_display(self, request: Any) -> tuple[Any, ...]:
        list_display = tuple(super().get_list_display(request))  # type: ignore[misc]
        list_display_links = tuple(getattr(self, "list_display_links", ()) or ())
        fk_map = self._fk_field_map()

        out: list[Any] = []
        for entry in list_display:
            if self._should_link(entry, fk_map, list_display_links):
                out.append(self._foreign_key_link(entry, fk_map[entry]))
            else:
                out.append(entry)
        return tuple(out)

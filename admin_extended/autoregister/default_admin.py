"""DefaultModelAdmin — auto-populates list_display, list_filter, select_related."""
from __future__ import annotations

from typing import Any

from django.db.models import JSONField, TextField

from ..core import ExtendedAdminModel

_END_OF_LIST_DISPLAY = ("created_at", "created", "modified_at", "modified")


class DefaultModelAdmin(ExtendedAdminModel):
    """ModelAdmin that picks sensible defaults from the model schema."""

    list_display_ignore_field_types: tuple[type, ...] = (TextField, JSONField)
    list_display_ignore_field_names: tuple[str, ...] = ()

    def __init__(self, model, admin_site):  # type: ignore[no-untyped-def]
        if self.list_display == ("__str__",):
            self.list_display = self._build_list_display(model)
        if not self.list_filter:
            self.list_filter = tuple(f.name for f in model._meta.fields if f.choices)
        super().__init__(model, admin_site)

    def _build_list_display(self, model: Any) -> tuple[str, ...]:
        cols: list[str] = ["__str__"]
        for field in model._meta.fields:
            if self._ignore(field):
                continue
            cols.append(field.name)
        # Move timestamps to the end
        for name in _END_OF_LIST_DISPLAY:
            if name in cols:
                cols.append(cols.pop(cols.index(name)))
        return tuple(cols)

    def _ignore(self, field: Any) -> bool:
        if field.name == "id":
            return True
        if isinstance(field, self.list_display_ignore_field_types):
            return True
        return field.name in self.list_display_ignore_field_names

    def get_queryset(self, request):  # type: ignore[no-untyped-def]
        qs = super().get_queryset(request)
        related = tuple(f.name for f in self.model._meta.fields if f.is_relation)  # type: ignore[attr-defined]
        if related:
            qs = qs.select_related(*related)
        return qs

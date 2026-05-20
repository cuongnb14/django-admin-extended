"""ObjectToolMixin — adds change-form and change-list action buttons."""
from __future__ import annotations

from typing import Any

from django.urls import path, reverse

from .decorator import ObjectToolSpec
from .views import check_permission, invoke


class ObjectToolMixin:
    change_form_tools: tuple[str, ...] = ()
    change_list_tools: tuple[str, ...] = ()

    # ---- URL registration ---------------------------------------------

    def get_urls(self):  # type: ignore[no-untyped-def]
        urls = super().get_urls()  # type: ignore[misc]
        base = f"{self.model._meta.app_label}_{self.model._meta.model_name}"  # type: ignore[attr-defined]
        custom = [
            path(
                "<path:object_id>/object-tools/<str:name>",
                self.admin_site.admin_view(self._change_form_object_tool_view),  # type: ignore[attr-defined]
                name=f"{base}_change_form_object_tool",
            ),
            path(
                "object-tools/<str:name>",
                self.admin_site.admin_view(self._change_list_object_tool_view),  # type: ignore[attr-defined]
                name=f"{base}_change_list_object_tool",
            ),
        ]
        return custom + urls

    # ---- spec lookup --------------------------------------------------

    def _resolve_specs(self, attr_names: tuple[str, ...]) -> dict[str, ObjectToolSpec]:
        out: dict[str, ObjectToolSpec] = {}
        for attr_name in attr_names:
            method = getattr(self, attr_name)
            spec: ObjectToolSpec | None = getattr(method, "object_tool", None)
            if spec is None:
                raise ValueError(
                    f"{type(self).__name__}.{attr_name} is referenced in tools but is not decorated with @object_tool"
                )
            out[spec.name] = spec
        return out

    def _change_form_specs(self) -> dict[str, ObjectToolSpec]:
        return self._resolve_specs(self.change_form_tools)

    def _change_list_specs(self) -> dict[str, ObjectToolSpec]:
        return self._resolve_specs(self.change_list_tools)

    # ---- dispatchers --------------------------------------------------

    def _change_form_object_tool_view(self, request, object_id, name):  # type: ignore[no-untyped-def]
        spec = self._change_form_specs()[name]
        obj = self.get_object(request, object_id)  # type: ignore[attr-defined]
        check_permission(spec, self, request, obj)
        return invoke(spec, self, request, object_id)

    def _change_list_object_tool_view(self, request, name):  # type: ignore[no-untyped-def]
        spec = self._change_list_specs()[name]
        check_permission(spec, self, request)
        return invoke(spec, self, request)

    # ---- template context ---------------------------------------------

    def _render_change_form_tools(self, request, object_id):  # type: ignore[no-untyped-def]
        base = f"{self.model._meta.app_label}_{self.model._meta.model_name}"  # type: ignore[attr-defined]
        in_object_tools: list[dict[str, Any]] = []
        in_submit_row: list[dict[str, Any]] = []
        for name, spec in self._change_form_specs().items():
            entry = {
                "icon": spec.icon,
                "label": spec.label,
                "url": reverse(f"admin:{base}_change_form_object_tool", args=[object_id, name]),
            }
            if spec.method == "GET":
                in_object_tools.append(entry)
            else:
                entry["post_param"] = spec.post_param
                in_submit_row.append(entry)
        return in_object_tools, in_submit_row

    def _render_change_list_tools(self, request):  # type: ignore[no-untyped-def]
        base = f"{self.model._meta.app_label}_{self.model._meta.model_name}"  # type: ignore[attr-defined]
        return [
            {
                "icon": spec.icon,
                "label": spec.label,
                "url": reverse(f"admin:{base}_change_list_object_tool", args=[name]),
            }
            for name, spec in self._change_list_specs().items()
        ]

    # ---- changeform_view / changelist_view -----------------------------

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):  # type: ignore[no-untyped-def]
        extra_context = dict(extra_context or {})
        if object_id is not None:
            object_tools, submit_row = self._render_change_form_tools(request, object_id)
            extra_context["admin_extended_object_tools"] = object_tools
            extra_context["admin_extended_submit_row_tools"] = submit_row
        return super().changeform_view(request, object_id, form_url, extra_context)  # type: ignore[misc]

    def changelist_view(self, request, extra_context=None):  # type: ignore[no-untyped-def]
        extra_context = dict(extra_context or {})
        extra_context["admin_extended_changelist_tools"] = self._render_change_list_tools(request)
        return super().changelist_view(request, extra_context)  # type: ignore[misc]

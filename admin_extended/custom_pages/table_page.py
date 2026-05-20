"""Custom table admin page that replaces the changelist with bespoke HTML."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from django.contrib import admin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import path


@dataclass
class TableData:
    header: str
    titles: list[str] = field(default_factory=list)
    rows: list[list[Any]] = field(default_factory=list)

    def add_row(self, row: list[Any]) -> None:
        self.rows.append(row)


class CustomTableAdminPage(admin.ModelAdmin):
    """ModelAdmin whose changelist is a custom table.

    Override ``get_table_data`` to return a list of ``TableData`` instances.
    """

    model: type | None = None

    def get_urls(self):  # type: ignore[no-untyped-def]
        if self.model is None:
            raise RuntimeError("CustomTableAdminPage subclasses must set 'model'")
        view_name = f"{self.model._meta.app_label}_{self.model._meta.model_name}_changelist"  # type: ignore[union-attr]
        return [path("", self._custom_view, name=view_name)]

    def get_table_data(self) -> list[TableData]:
        raise NotImplementedError

    def _custom_view(self, request: HttpRequest) -> HttpResponse:
        context = {
            **admin.site.each_context(request),
            "tables": self.get_table_data(),
        }
        return render(request, "admin/admin_extended/custom_pages/custom_table_page.html", context)

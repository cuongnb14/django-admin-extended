"""View helpers shared by ObjectToolMixin."""
from __future__ import annotations

from typing import Any

from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse

from .decorator import ObjectToolSpec


def check_permission(spec: ObjectToolSpec, model_admin: Any, request: HttpRequest, obj: Any = None) -> None:
    if spec.require_permission is None:
        return
    if spec.require_permission == "view":
        # Use Django's base ModelAdmin permission check (bypasses page-mode overrides).
        if not admin.ModelAdmin.has_view_permission(model_admin, request, obj):
            raise PermissionDenied
    elif spec.require_permission == "change":
        # Use Django's base ModelAdmin permission check (bypasses page-mode overrides).
        if not admin.ModelAdmin.has_change_permission(model_admin, request, obj):
            raise PermissionDenied


def invoke(spec: ObjectToolSpec, model_admin: Any, request: HttpRequest, *args: Any) -> HttpResponse:
    return spec.func(model_admin, request, *args)

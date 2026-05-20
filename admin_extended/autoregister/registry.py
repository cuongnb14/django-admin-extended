"""auto_register — register every non-Django model with a default admin."""
from __future__ import annotations

from collections.abc import Iterable

from django.apps import apps
from django.contrib import admin

from .default_admin import DefaultModelAdmin


def auto_register(
    *,
    default_admin: type[admin.ModelAdmin] = DefaultModelAdmin,
    ignore: Iterable[str] | None = None,
    site: admin.AdminSite | None = None,
) -> None:
    """Register every model from non-Django apps that is not already registered.

    Args:
        default_admin: ModelAdmin class to register each model with.
        ignore: identifiers ``'app_label.ModelName'`` to skip.
        site: AdminSite to register into (defaults to ``admin.site``).
    """
    ignore_set = {x.lower() for x in (ignore or ())}
    target_site = site or admin.site

    for model in apps.get_models():
        identity = f"{model._meta.app_label}.{model.__name__}".lower()
        if model.__module__.startswith("django."):
            continue
        if identity in ignore_set:
            continue
        try:
            target_site.register(model, default_admin)
        except admin.sites.AlreadyRegistered:
            continue

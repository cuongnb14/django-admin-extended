"""Sidebar app/model ordering + bookmark section (cached + tolerant of missing sub-app)."""
from __future__ import annotations

from typing import Any

from django import template
from django.apps import apps as django_apps
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from ..conf import settings as ae_settings

register = template.Library()

_BOOKMARK_CACHE_KEY = "admin_extended:bookmarks:active"


def _load_bookmark_app_entry() -> dict[str, Any] | None:
    if not django_apps.is_installed("admin_extended.bookmarks"):
        return None
    cached = cache.get(_BOOKMARK_CACHE_KEY)
    if cached is not None:
        return cached if cached else None
    Bookmark = django_apps.get_model("admin_extended_bookmarks", "Bookmark")
    bookmarks = list(Bookmark.objects.filter(is_active=True).order_by("order"))
    if not bookmarks:
        cache.set(_BOOKMARK_CACHE_KEY, {}, ae_settings.BOOKMARK_CACHE_SECONDS)
        return None
    entry = {
        "name": "Bookmark",
        "icon": "fas fa-bookmark",
        "app_label": "admin_extended_bookmarks",
        "app_url": "/admin/admin_extended_bookmarks/bookmark/",
        "has_module_perms": True,
        "models": [
            {
                "name": b.name,
                "object_name": b.name,
                "perms": {"add": False, "change": False, "delete": False, "view": True},
                "admin_url": b.url,
                "view_only": True,
            }
            for b in bookmarks
        ],
    }
    cache.set(_BOOKMARK_CACHE_KEY, entry, ae_settings.BOOKMARK_CACHE_SECONDS)
    return entry


def _attach_metadata(app: dict[str, Any]) -> dict[str, Any]:
    out = dict(app)
    if out.get("app_label") == "auth":
        out["name"] = "Groups"
    icon_map = ae_settings.APP_ICON
    out["icon"] = icon_map.get(out.get("app_label"), ae_settings.DEFAULT_APP_ICON)
    return out


@register.filter
def sort_apps(apps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    order = ae_settings.MENU_APP_ORDER
    max_index = len(order)
    decorated = [_attach_metadata(a) for a in apps]
    decorated.sort(key=lambda a: order.index(a["app_label"]) if a["app_label"] in order else max_index)

    bookmark_entry = _load_bookmark_app_entry()
    if bookmark_entry:
        return [bookmark_entry, *decorated]
    return decorated


@register.filter
def sort_models(models_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    order = ae_settings.MENU_MODEL_ORDER
    max_index = len(order)
    return sorted(
        models_list,
        key=lambda m: order.index(m["object_name"]) if m["object_name"] in order else max_index,
    )


# ---- cache invalidation on Bookmark write ---------------------------------

if django_apps.is_installed("admin_extended.bookmarks"):
    Bookmark = django_apps.get_model("admin_extended_bookmarks", "Bookmark")

    @receiver(post_save, sender=Bookmark)
    @receiver(post_delete, sender=Bookmark)
    def _invalidate_bookmark_cache(sender, **kwargs):  # type: ignore[no-untyped-def]
        cache.delete(_BOOKMARK_CACHE_KEY)

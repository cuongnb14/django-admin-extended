"""Lazy settings proxy.

Reads from ``django.conf.settings.ADMIN_EXTENDED`` on every attribute access,
so ``override_settings`` works correctly during tests.
"""
from __future__ import annotations

from typing import Any

from django.conf import settings as django_settings

_DEFAULTS: dict[str, Any] = {
    "MENU_APP_ORDER": [],
    "MENU_MODEL_ORDER": [],
    "APP_ICON": {},
    "TABBED_INLINES": True,
    "AUTO_RAW_ID_FIELDS": False,
    "DEFAULT_APP_ICON": "fas fa-layer-group",
    "BOOKMARK_CACHE_SECONDS": 60,
}


class AdminExtendedSettings:
    def __getattr__(self, name: str) -> Any:
        if name not in _DEFAULTS:
            raise AttributeError(f"AdminExtendedSettings has no attribute {name!r}")
        user_overrides = getattr(django_settings, "ADMIN_EXTENDED", {})
        return user_overrides.get(name, _DEFAULTS[name])


settings = AdminExtendedSettings()

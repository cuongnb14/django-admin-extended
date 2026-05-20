"""Generic helpers: read arbitrary Django settings inside templates."""
from __future__ import annotations

from typing import Any

from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def settings_value(name: str, default: Any = None) -> Any:
    if "." not in name:
        return getattr(settings, name, default)
    head, *rest = name.split(".")
    value: Any = getattr(settings, head, None)
    for key in rest:
        if not isinstance(value, dict) or key not in value:
            return default
        value = value[key]
    return value

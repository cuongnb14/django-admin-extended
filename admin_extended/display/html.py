"""HTML rendering helpers for admin display methods."""
from __future__ import annotations

import json
from typing import Any

from django.utils.html import format_html
from django.utils.safestring import SafeString, mark_safe

SUCCESS = "#3d9402"
ERROR = "#f20707"
WARNING = "#ffad00"
DEFAULT = "#818181"


def html_img(url: str | None, href: str | None = None, height: str = "200px") -> SafeString | str:
    """Return an <img> tag, optionally wrapped in <a>, or '-' if url is falsy."""
    if not url:
        return "-"
    if href:
        return format_html('<a href="{}" target="_blank"><img height="{}" src="{}" /></a>', href, height, url)
    return format_html('<img height="{}" src="{}" />', height, url)


def html_link(url: str, title: str | None = None, target: str = "_blank", css_class: str = "") -> SafeString:
    """Return an <a> tag; if title is omitted, the URL itself is the visible text."""
    visible = title if title is not None else url
    return format_html('<a href="{}" class="{}" target="{}">{}</a>', url, css_class, target, visible)


def html_color(text: str, color: str) -> SafeString:
    """Return a bold-colored span around the text."""
    return format_html('<b style="color:{};">{}</b>', color, text)


def html_json(content: Any, indent: int = 4) -> SafeString:
    """Pretty-print JSON inside a <pre> tag."""
    raw = json.dumps(content, indent=indent, default=str)
    return mark_safe(f"<pre>{raw}</pre>")

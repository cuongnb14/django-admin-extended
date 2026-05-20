"""Tests for free HTML helper functions."""
from __future__ import annotations

from django.utils.safestring import SafeString

from admin_extended.display import html_color, html_img, html_json, html_link
from admin_extended.display.html import DEFAULT, ERROR, SUCCESS, WARNING


def test_html_img_returns_safe_html():
    out = html_img("https://example.com/a.png", height="40px")
    assert isinstance(out, SafeString)
    assert 'src="https://example.com/a.png"' in out
    assert 'height="40px"' in out


def test_html_img_returns_dash_for_empty_url():
    assert html_img("") == "-"
    assert html_img(None) == "-"


def test_html_img_with_href_wraps_in_anchor():
    out = html_img("https://x/i.png", href="https://x/page")
    assert '<a href="https://x/page"' in out
    assert "<img" in out


def test_html_link_uses_url_as_title_when_omitted():
    out = html_link("https://x")
    assert ">https://x<" in out


def test_html_link_uses_custom_title():
    out = html_link("https://x", title="Click")
    assert ">Click<" in out


def test_html_color_renders_bold_with_color():
    out = html_color("OK", SUCCESS)
    assert "<b" in out and ">OK<" in out and "color:#3d9402" in out


def test_html_json_pretty_prints_in_pre():
    out = html_json({"a": 1, "b": [2, 3]})
    assert out.startswith("<pre>")
    assert '"a": 1' in out


def test_color_constants_are_strings():
    assert all(isinstance(c, str) for c in (SUCCESS, ERROR, WARNING, DEFAULT))

"""Tests for the sidebar menu templatetag."""
from __future__ import annotations

import pytest
from django.core.cache import cache
from django.test import override_settings

from admin_extended.bookmarks.models import Bookmark
from admin_extended.templatetags.admin_extended_menu import sort_apps, sort_models

_BOOKMARK_CACHE_KEY = "admin_extended:bookmarks:active"


@pytest.fixture(autouse=True)
def clear_bookmark_cache():
    cache.delete(_BOOKMARK_CACHE_KEY)
    yield
    cache.delete(_BOOKMARK_CACHE_KEY)


@override_settings(ADMIN_EXTENDED={
    "MENU_APP_ORDER": ["sample_app", "auth"],
    "APP_ICON": {"sample_app": "fas fa-flask"},
})
def test_sort_apps_respects_order_and_icon(db):
    apps = [
        {"app_label": "auth", "name": "Auth"},
        {"app_label": "sample_app", "name": "Sample"},
        {"app_label": "other", "name": "Other"},
    ]
    sorted_apps = sort_apps(apps)
    labels = [a["app_label"] for a in sorted_apps]
    # sample_app first, auth second, other last
    assert labels.index("sample_app") < labels.index("auth") < labels.index("other")
    assert next(a for a in sorted_apps if a["app_label"] == "sample_app")["icon"] == "fas fa-flask"


def test_sort_apps_returns_new_list_does_not_mutate_input(db):
    apps = [{"app_label": "z"}, {"app_label": "a"}]
    out = sort_apps(apps)
    # input is preserved
    assert [a["app_label"] for a in apps] == ["z", "a"]
    assert out is not apps


def test_sort_apps_prepends_bookmark_app_when_bookmarks_exist(db):
    Bookmark.objects.create(name="B", url="https://b", is_active=True, order=1)
    apps = [{"app_label": "sample_app", "name": "Sample"}]
    out = sort_apps(apps)
    assert out[0]["app_label"] == "admin_extended_bookmarks"
    assert out[0]["models"][0]["name"] == "B"


def test_sort_models_orders_by_setting(db):
    with override_settings(ADMIN_EXTENDED={"MENU_MODEL_ORDER": ["Product", "Order"]}):
        models_list = [{"object_name": "Order"}, {"object_name": "Product"}, {"object_name": "Customer"}]
        out = sort_models(models_list)
        names = [m["object_name"] for m in out]
        assert names.index("Product") < names.index("Order") < names.index("Customer")

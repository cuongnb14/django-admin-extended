"""Tests for bookmarks sub-app."""
from __future__ import annotations

from django.urls import reverse

from admin_extended.bookmarks.models import Bookmark


def test_bookmark_str_returns_name(db):
    b = Bookmark.objects.create(name="Docs", url="https://example.com")
    assert str(b) == "Docs"


def test_admin_changelist_renders(admin_client, db):
    Bookmark.objects.create(name="A", url="https://a/")
    url = reverse("admin:admin_extended_bookmarks_bookmark_changelist")
    response = admin_client.get(url)
    assert response.status_code == 200


def test_admin_create_via_changeform(admin_client, db):
    url = reverse("admin:admin_extended_bookmarks_bookmark_add")
    response = admin_client.post(
        url,
        data={"name": "New", "url": "https://x/", "is_active": "on", "order": "0", "_save": "Save"},
    )
    assert response.status_code in (200, 302)
    assert Bookmark.objects.filter(name="New").exists()

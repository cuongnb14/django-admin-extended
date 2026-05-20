"""Bookmark admin — plain ModelAdmin, no custom endpoints."""
from __future__ import annotations

from django.contrib import admin

from .models import Bookmark


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ("name", "url", "is_active", "order")
    list_filter = ("is_active",)
    list_editable = ("is_active", "order")
    search_fields = ("name", "url")

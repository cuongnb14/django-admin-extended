"""Reusable admin actions."""
from __future__ import annotations

from django.contrib import admin, messages


@admin.action(description="Delete selected without confirm")
def delete_without_confirm(modeladmin, request, queryset):  # noqa: ARG001
    deleted, _ = queryset.delete()
    messages.success(request, f"Deleted {deleted} record(s)")

from __future__ import annotations

from django.apps import AppConfig


class AdminExtendedConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "admin_extended"
    label = "admin_extended"
    verbose_name = "Admin Extended"

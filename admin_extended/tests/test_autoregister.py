"""Tests for autoregister subsystem."""
from __future__ import annotations

from django.contrib import admin
from django.db import models

from admin_extended.autoregister import DefaultModelAdmin, auto_register
from admin_extended.tests.example_project.sample_app.models import Order, Product


def test_default_list_display_excludes_text_and_json_fields():
    site = admin.AdminSite(name="auto1")
    site.register(Product, DefaultModelAdmin)
    ma = site._registry[Product]

    # 'notes' is TextField -> excluded; 'status' has choices -> included
    assert "name" in ma.list_display
    assert "price" in ma.list_display
    assert "status" in ma.list_display
    assert "notes" not in ma.list_display


def test_default_list_filter_picks_choice_fields():
    site = admin.AdminSite(name="auto2")
    site.register(Product, DefaultModelAdmin)
    ma = site._registry[Product]
    assert tuple(ma.list_filter) == ("status",)


def test_default_select_related_for_fks():
    from django.test import RequestFactory

    site = admin.AdminSite(name="auto3")
    site.register(Order, DefaultModelAdmin)
    ma = site._registry[Order]
    request = RequestFactory().get("/")
    qs = ma.get_queryset(request)
    assert set(qs.query.select_related) >= {"customer", "product"}


def test_auto_register_skips_django_models():
    site = admin.AdminSite(name="auto4")
    auto_register(default_admin=DefaultModelAdmin, ignore=[], site=site)
    registered_modules = {model.__module__ for model in site._registry}
    assert not any(m.startswith("django.") for m in registered_modules)


def test_auto_register_respects_ignore_in_canonical_app_dot_model_format():
    site = admin.AdminSite(name="auto5")
    auto_register(default_admin=DefaultModelAdmin, ignore=["sample_app.Product"], site=site)
    assert Product not in site._registry
    # Other sample_app models still registered
    assert Order in site._registry

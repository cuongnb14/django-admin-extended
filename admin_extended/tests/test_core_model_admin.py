"""Integration tests for ExtendedModelAdmin using sample_app."""
from __future__ import annotations

from django.contrib import admin
from django.test import RequestFactory

from admin_extended.core import ExtendedModelAdmin, PageMode, get_page_mode
from admin_extended.tests.example_project.sample_app.models import Customer, Order, Product


def _site_with(*models_admins):
    site = admin.AdminSite(name=f"test_{id(models_admins)}")
    for model, model_admin_cls in models_admins:
        site.register(model, model_admin_cls)
    return site


def test_view_mode_has_change_permission_is_false(superuser):
    class ProductAdmin(ExtendedModelAdmin):
        pass

    site = _site_with((Product, ProductAdmin))
    pa = site._registry[Product]

    request = RequestFactory().get("/admin/sample_app/product/1/change/")
    request.user = superuser
    product = Product(name="x", price=1)

    # In view mode (no ?edit) the admin must report no change permission.
    assert get_page_mode(request, object_id=1) is PageMode.VIEW
    assert pa.has_change_permission(request, product) is False


def test_edit_mode_has_change_permission_is_true(superuser):
    class ProductAdmin(ExtendedModelAdmin):
        pass

    site = _site_with((Product, ProductAdmin))
    pa = site._registry[Product]

    request = RequestFactory().get("/admin/sample_app/product/1/change/?edit=1")
    request.user = superuser
    product = Product(name="x", price=1)

    assert get_page_mode(request, object_id=1) is PageMode.EDIT
    assert pa.has_change_permission(request, product) is True


def test_super_admin_only_fields_hidden_from_non_superuser(user):
    class ProductAdmin(ExtendedModelAdmin):
        list_display = ("name", "price", "status")
        superuser_only_fields = ("status",)

    site = _site_with((Product, ProductAdmin))
    pa = site._registry[Product]

    request = RequestFactory().get("/")
    request.user = user  # staff but not superuser
    assert "status" not in pa.get_list_display(request)


def test_super_admin_only_fields_visible_to_superuser(superuser):
    class ProductAdmin(ExtendedModelAdmin):
        list_display = ("name", "price", "status")
        superuser_only_fields = ("status",)

    site = _site_with((Product, ProductAdmin))
    pa = site._registry[Product]

    request = RequestFactory().get("/")
    request.user = superuser
    assert "status" in pa.get_list_display(request)

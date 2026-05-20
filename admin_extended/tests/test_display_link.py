"""Tests for the FK list_display link adapter (covers B7 regression)."""
from __future__ import annotations

from django.contrib import admin
from django.test import RequestFactory

from admin_extended.display import DisplayLinkAdapter
from admin_extended.tests.example_project.sample_app.models import Customer, Order


class _DummyAdmin(DisplayLinkAdapter, admin.ModelAdmin):
    model = Order

    def get_list_display(self, request):
        return super().get_list_display(request)


def test_fk_field_converted_to_link_when_not_in_list_display_links(admin_site=None):
    site = admin.AdminSite(name="dummy")
    site.register(Customer)
    site.register(Order, _DummyAdmin)
    order_admin = site._registry[Order]
    order_admin.list_display = ("id", "customer", "product", "quantity")
    order_admin.list_display_links = ("id",)

    request = RequestFactory().get("/")
    result = order_admin.get_list_display(request)

    # customer and product are FKs, NOT in list_display_links -> converted to callables
    assert callable(result[1])
    assert callable(result[2])
    # id is in list_display_links -> kept as string
    assert result[0] == "id"
    # quantity is not FK -> kept as string
    assert result[3] == "quantity"


def test_does_not_skip_first_element_b7_regression():
    """v5 used list_display[0] unconditionally; v6 must process index 0 too."""
    site = admin.AdminSite(name="dummy2")
    site.register(Customer)
    site.register(Order, _DummyAdmin)
    order_admin = site._registry[Order]
    # customer is at index 0 AND not in list_display_links -> must become callable
    order_admin.list_display = ("customer", "quantity")
    order_admin.list_display_links = ()

    request = RequestFactory().get("/")
    result = order_admin.get_list_display(request)
    assert callable(result[0])


def test_enable_foreign_link_false_skips_conversion():
    site = admin.AdminSite(name="dummy3")
    site.register(Customer)

    class A(DisplayLinkAdapter, admin.ModelAdmin):
        model = Order
        enable_foreign_link = False
        list_display = ("customer", "quantity")
        list_display_links = ()

        def get_list_display(self, request):
            return super().get_list_display(request)

    site.register(Order, A)
    admin_inst = site._registry[Order]
    request = RequestFactory().get("/")
    result = admin_inst.get_list_display(request)
    assert result == ("customer", "quantity")

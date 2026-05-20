"""Tests for the object_tools subsystem."""
from __future__ import annotations

import pytest

from admin_extended.object_tools import ObjectToolMixin, ObjectToolSpec, object_tool


def test_decorator_attaches_spec_with_defaults():
    @object_tool(label="Recompute")
    def recompute(self, request, object_id):
        return "ok"

    spec: ObjectToolSpec = recompute.object_tool  # type: ignore[attr-defined]
    assert spec.label == "Recompute"
    assert spec.name == "recompute"
    assert spec.icon is None
    assert spec.method == "GET"
    assert spec.post_param is None
    assert spec.require_permission == "change"


def test_decorator_accepts_all_options():
    @object_tool(
        label="Export",
        icon="fas fa-download",
        method="POST",
        post_param="reason",
        require_permission="view",
        name="custom_name",
    )
    def export(self, request):
        return "ok"

    spec = export.object_tool  # type: ignore[attr-defined]
    assert spec.name == "custom_name"
    assert spec.icon == "fas fa-download"
    assert spec.method == "POST"
    assert spec.post_param == "reason"
    assert spec.require_permission == "view"


def test_decorator_rejects_invalid_method():
    with pytest.raises(ValueError, match="method"):
        @object_tool(label="Bad", method="DELETE")  # type: ignore[arg-type]
        def bad(self, request):
            ...


def test_decorator_rejects_invalid_permission():
    with pytest.raises(ValueError, match="require_permission"):
        @object_tool(label="Bad", require_permission="superpower")  # type: ignore[arg-type]
        def bad(self, request):
            ...


# ----- mixin dispatch tests -----

from django.contrib import admin
from django.http import HttpResponse
from django.urls import reverse

from admin_extended.core import ExtendedAdminModel
from admin_extended.tests.example_project.sample_app.models import Product


class _ProductAdmin(ExtendedAdminModel):
    change_form_tools = ("recompute",)
    change_list_tools = ("export",)

    @object_tool(label="Recompute", icon="fas fa-sync")
    def recompute(self, request, object_id):
        return HttpResponse(f"recomputed {object_id}")

    @object_tool(label="Export CSV", method="POST", post_param="reason", require_permission="view")
    def export(self, request):
        return HttpResponse("exported")


def _register(model, admin_cls):
    if model in admin.site._registry:
        admin.site.unregister(model)
    admin.site.register(model, admin_cls)


def test_change_form_object_tool_dispatch(admin_client, db):
    _register(Product, _ProductAdmin)
    product = Product.objects.create(name="p", price=10)

    url = reverse("admin:sample_app_product_change_form_object_tool", args=[product.pk, "recompute"])
    response = admin_client.get(url)
    assert response.status_code == 200
    assert response.content == f"recomputed {product.pk}".encode()


def test_change_list_object_tool_dispatch(admin_client, db):
    _register(Product, _ProductAdmin)
    url = reverse("admin:sample_app_product_change_list_object_tool", args=["export"])
    response = admin_client.post(url, data={"reason": "test"})
    assert response.status_code == 200
    assert response.content == b"exported"


def test_change_form_tool_denied_without_permission(client, user, db):
    # `user` is staff but has no Product.change permission
    _register(Product, _ProductAdmin)
    client.force_login(user)
    product = Product.objects.create(name="p", price=10)
    url = reverse("admin:sample_app_product_change_form_object_tool", args=[product.pk, "recompute"])
    response = client.get(url)
    assert response.status_code == 403

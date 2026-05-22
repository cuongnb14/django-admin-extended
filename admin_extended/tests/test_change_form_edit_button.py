"""Edit-button visibility on the view-mode changeform.

Regression: with view-mode ``has_change_permission`` short-circuited to False
on ``ExtendedModelAdmin``, the template gated the Edit button on
``has_change_permission or has_delete_permission`` — which hid the button for
users who had change permission but not delete permission.
"""
from __future__ import annotations

import importlib

import pytest
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import Client
from django.urls import clear_url_caches, reverse

from admin_extended.core import ExtendedModelAdmin
from admin_extended.tests.example_project.sample_app.models import Product


class _PlainProductAdmin(ExtendedModelAdmin):
    pass


def _register(model, admin_cls):
    if model in admin.site._registry:
        admin.site.unregister(model)
    admin.site.register(model, admin_cls)
    importlib.reload(importlib.import_module(settings.ROOT_URLCONF))
    clear_url_caches()


def _grant(user, codenames):
    ct = ContentType.objects.get_for_model(Product)
    for codename in codenames:
        user.user_permissions.add(
            Permission.objects.get(content_type=ct, codename=codename)
        )


@pytest.fixture
def staff_user(db):
    User = get_user_model()
    return User.objects.create_user(username="staff", password="pw", is_staff=True)


def _client_for(user):
    c = Client()
    c.force_login(user)
    return c


def _view_url(product):
    return reverse("admin:sample_app_product_change", args=[product.pk])


# Unique marker for the rendered Edit button:
# <a href="?edit=1"><i class="fas fa-edit"></i> Edit</a>
EDIT_BTN_MARKER = 'fa-edit"></i> Edit'


def test_change_only_user_sees_edit_button_in_view_mode(staff_user):
    _register(Product, _PlainProductAdmin)
    _grant(staff_user, ["view_product", "change_product"])
    product = Product.objects.create(name="x", price=1)

    html = _client_for(staff_user).get(_view_url(product)).content.decode()

    assert EDIT_BTN_MARKER in html


def test_delete_only_user_does_not_see_edit_button(staff_user):
    _register(Product, _PlainProductAdmin)
    _grant(staff_user, ["view_product", "delete_product"])
    product = Product.objects.create(name="x", price=1)

    html = _client_for(staff_user).get(_view_url(product)).content.decode()

    assert EDIT_BTN_MARKER not in html


def test_view_only_user_does_not_see_edit_button(staff_user):
    _register(Product, _PlainProductAdmin)
    _grant(staff_user, ["view_product"])
    product = Product.objects.create(name="x", price=1)

    html = _client_for(staff_user).get(_view_url(product)).content.decode()

    assert EDIT_BTN_MARKER not in html

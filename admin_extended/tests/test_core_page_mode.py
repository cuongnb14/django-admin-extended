"""Tests for PageMode + ContextVar."""
from __future__ import annotations

from django.test import RequestFactory

from admin_extended.core.page_mode import PageMode, current_page_mode, get_page_mode, page_mode_scope


def test_page_mode_enum_values():
    assert PageMode.VIEW == "view"
    assert PageMode.EDIT == "edit"
    assert PageMode.ADD == "add"


def test_get_page_mode_classifies_add_when_no_object_id():
    request = RequestFactory().get("/admin/sample_app/order/add/")
    assert get_page_mode(request, object_id=None) is PageMode.ADD


def test_get_page_mode_classifies_view_when_object_id_and_no_edit_param():
    request = RequestFactory().get("/admin/sample_app/order/1/change/")
    assert get_page_mode(request, object_id="1") is PageMode.VIEW


def test_get_page_mode_classifies_edit_when_edit_param_set():
    request = RequestFactory().get("/admin/sample_app/order/1/change/?edit=1")
    assert get_page_mode(request, object_id="1") is PageMode.EDIT


def test_get_page_mode_classifies_edit_when_popup_param_set():
    request = RequestFactory().get("/admin/sample_app/order/1/change/?_popup=1")
    assert get_page_mode(request, object_id="1") is PageMode.EDIT


def test_page_mode_scope_sets_and_resets_context_var():
    assert current_page_mode() is None
    with page_mode_scope(PageMode.VIEW):
        assert current_page_mode() is PageMode.VIEW
        with page_mode_scope(PageMode.EDIT):
            assert current_page_mode() is PageMode.EDIT
        assert current_page_mode() is PageMode.VIEW
    assert current_page_mode() is None


def test_page_mode_scope_resets_on_exception():
    try:
        with page_mode_scope(PageMode.VIEW):
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    assert current_page_mode() is None

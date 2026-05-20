"""Tests for the lazy settings proxy."""
from __future__ import annotations

import pytest
from django.test import override_settings

from admin_extended.conf import settings as ae_settings


def test_defaults_returned_when_user_did_not_configure():
    assert ae_settings.MENU_APP_ORDER == []
    assert ae_settings.MENU_MODEL_ORDER == []
    assert ae_settings.APP_ICON == {}
    assert ae_settings.TABBED_INLINES is True
    assert ae_settings.AUTO_RAW_ID_FIELDS is False
    assert ae_settings.DEFAULT_APP_ICON == "fas fa-layer-group"
    assert ae_settings.BOOKMARK_CACHE_SECONDS == 60


@override_settings(ADMIN_EXTENDED={"TABBED_INLINES": False, "APP_ICON": {"sample_app": "fas fa-flask"}})
def test_user_overrides_take_precedence():
    assert ae_settings.TABBED_INLINES is False
    assert ae_settings.APP_ICON == {"sample_app": "fas fa-flask"}
    # Unconfigured keys still return defaults
    assert ae_settings.AUTO_RAW_ID_FIELDS is False


def test_override_settings_is_reactive():
    """Changes to settings.ADMIN_EXTENDED at runtime must be observable."""
    assert ae_settings.TABBED_INLINES is True
    with override_settings(ADMIN_EXTENDED={"TABBED_INLINES": False}):
        assert ae_settings.TABBED_INLINES is False
    assert ae_settings.TABBED_INLINES is True


def test_unknown_attribute_raises():
    with pytest.raises(AttributeError):
        ae_settings.DOES_NOT_EXIST

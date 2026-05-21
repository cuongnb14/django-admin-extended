"""ExtendedModelAdmin — the main base class consumers subclass.

Composes:
  * ``DisplayLinkAdapter``  -> FK columns become links
  * Fieldset filtering by ``PageMode`` and ``superuser_only_fields``
  * View / Edit / Add page-mode classification via ``ContextVar``
  * Tabbed inlines (``tabbed_inlines``)
  * Auto raw_id/autocomplete (``auto_raw_id_fields``)
  * Optional ``skip_delete_confirm`` action override
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from django.contrib import admin
from django.http import HttpRequest

from ..conf import settings as ae_settings
from ..display.link_adapter import DisplayLinkAdapter
from ..object_tools.mixin import ObjectToolMixin
from .actions import delete_without_confirm
from .field_visibility import filter_fieldsets, is_display_only
from .page_mode import PageMode, get_page_mode, page_mode_scope


def _has_search_fields(field) -> bool:  # type: ignore[no-untyped-def]
    model_admin = admin.site._registry.get(field.related_model)
    return bool(model_admin and model_admin.search_fields)


class ExtendedModelAdmin(ObjectToolMixin, DisplayLinkAdapter, admin.ModelAdmin):
    """Drop-in replacement for ``admin.ModelAdmin`` with v6 features.

    Class attributes:
        view_only_fields:        fields shown only in VIEW mode
        edit_only_fields:        fields shown only in EDIT / ADD mode
        superuser_only_fields:   fields hidden from non-superusers (both list & form)
        tabbed_inlines:          render inlines as tabs (default from settings)
        skip_delete_confirm:     replace delete_selected with no-confirm variant
        auto_raw_id_fields:      auto-set autocomplete/raw_id for all FKs
    """

    view_only_fields: tuple[str, ...] = ()
    edit_only_fields: tuple[str, ...] = ()
    superuser_only_fields: tuple[str, ...] = ()

    tabbed_inlines: bool = True
    skip_delete_confirm: bool = False
    auto_raw_id_fields: bool = False

    def __init__(self, model, admin_site) -> None:  # type: ignore[no-untyped-def]
        # Pull settings-backed defaults *at instantiation*, not import time,
        # so override_settings in tests is honored.
        if type(self).tabbed_inlines is True and "tabbed_inlines" not in type(self).__dict__:
            self.tabbed_inlines = ae_settings.TABBED_INLINES
        if type(self).auto_raw_id_fields is False and "auto_raw_id_fields" not in type(self).__dict__:
            self.auto_raw_id_fields = ae_settings.AUTO_RAW_ID_FIELDS

        if self.auto_raw_id_fields:
            self.autocomplete_fields, self.raw_id_fields = self._compute_raw_id_fields(model)

        super().__init__(model, admin_site)

    @staticmethod
    def _compute_raw_id_fields(model) -> tuple[tuple[str, ...], tuple[str, ...]]:  # type: ignore[no-untyped-def]
        ac = tuple(f.name for f in model._meta.fields if f.is_relation and _has_search_fields(f))
        ri = tuple(f.name for f in model._meta.fields if f.is_relation and not _has_search_fields(f))
        return ac, ri

    # ---- page mode integration ----------------------------------------

    def _changeform_view(self, request, object_id, form_url, extra_context):  # type: ignore[no-untyped-def]
        mode = get_page_mode(request, object_id)
        extra_context = {**(extra_context or {}), "ae_page_mode": mode.value}
        with page_mode_scope(mode):
            return super()._changeform_view(request, object_id, form_url, extra_context)

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        # Use obj is not None (not obj.pk) as the "not ADD" signal.
        # An unsaved obj (pk=None) passed from tests is still a valid "existing
        # object context" — we use a sentinel so get_page_mode classifies it as
        # VIEW or EDIT (not ADD) based on the request query string.
        if obj is not None and get_page_mode(request, obj.pk or "_") is PageMode.VIEW:
            return False
        return super().has_change_permission(request, obj)

    # ---- fieldset filtering -------------------------------------------

    def get_fieldsets(self, request: HttpRequest, obj: Any = None):  # type: ignore[no-untyped-def]
        fieldsets = list(super().get_fieldsets(request, obj))
        # Use obj is not None as the "existing object" signal (same as has_change_permission),
        # so unsaved objects don't accidentally classify as ADD.
        object_id = obj.pk or "_" if obj is not None else None
        mode = get_page_mode(request, object_id=object_id)
        fieldsets = self._filter_by_mode(mode, fieldsets)
        fieldsets = self._filter_by_user(request, fieldsets)
        return fieldsets

    def _filter_by_mode(self, mode: PageMode, fieldsets):  # type: ignore[no-untyped-def]
        if mode is PageMode.VIEW:
            if self.edit_only_fields:
                return filter_fieldsets(fieldsets, lambda f: f in self.edit_only_fields)
            return fieldsets
        # EDIT / ADD: hide read-only-style fields
        ro: Iterable[str] = self.view_only_fields
        return filter_fieldsets(fieldsets, lambda f: is_display_only(f, ro))

    def _filter_by_user(self, request: HttpRequest, fieldsets):  # type: ignore[no-untyped-def]
        if request.user.is_superuser:
            return fieldsets
        return filter_fieldsets(fieldsets, lambda f: f in self.superuser_only_fields)

    # ---- list_display superuser filtering -----------------------------

    def get_list_display(self, request: HttpRequest):  # type: ignore[no-untyped-def]
        list_display = super().get_list_display(request)
        if request.user.is_superuser:
            return list_display
        return tuple(x for x in list_display if x not in self.superuser_only_fields)

    # ---- delete-without-confirm action --------------------------------

    def get_actions(self, request: HttpRequest):  # type: ignore[no-untyped-def]
        actions = super().get_actions(request)
        if self.skip_delete_confirm:
            actions.pop("delete_selected", None)
            actions["delete_without_confirm"] = self.get_action(delete_without_confirm)
        return actions

    # ---- tabbed inlines flag -----------------------------------------

    def get_inline_instances(self, request: HttpRequest, obj: Any = None):  # type: ignore[no-untyped-def]
        request.is_tabbed_admin_extended = self.tabbed_inlines  # type: ignore[attr-defined]
        return super().get_inline_instances(request, obj)

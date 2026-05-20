"""Tests for fieldset-filtering helpers."""
from __future__ import annotations

from admin_extended.core.field_visibility import (
    filter_fieldsets,
    is_display_only,
)


def _sample_fieldsets():
    return [
        (None, {"fields": ("name", "status", "display_summary", "internal_notes")}),
        ("Meta", {"fields": (("created_at", "modified_at"), "secret_flag")}),
    ]


def test_is_display_only_true_for_display_prefix():
    assert is_display_only("display_summary", read_only_fields=set())
    assert is_display_only("display_anything", read_only_fields=set())


def test_is_display_only_true_for_explicit_read_only():
    assert is_display_only("summary", read_only_fields={"summary"})


def test_is_display_only_false_for_regular_field():
    assert not is_display_only("name", read_only_fields=set())


def test_filter_fieldsets_removes_by_predicate():
    fieldsets = _sample_fieldsets()
    result = filter_fieldsets(fieldsets, lambda f: f in {"secret_flag", "display_summary"})

    assert result == [
        (None, {"fields": ("name", "status", "internal_notes")}),
        ("Meta", {"fields": (("created_at", "modified_at"),)}),
    ]


def test_filter_fieldsets_drops_empty_field_groups():
    fieldsets = [("Meta", {"fields": (("a", "b"),)})]
    result = filter_fieldsets(fieldsets, lambda f: f in {"a", "b"})
    assert result == [("Meta", {"fields": ()})]


def test_filter_fieldsets_does_not_mutate_input():
    fieldsets = _sample_fieldsets()
    snapshot = [(name, dict(opts)) for name, opts in fieldsets]
    filter_fieldsets(fieldsets, lambda f: f in {"secret_flag"})
    for (orig_name, orig_opts), (snap_name, snap_opts) in zip(fieldsets, snapshot):
        assert orig_name == snap_name
        assert orig_opts["fields"] == snap_opts["fields"]

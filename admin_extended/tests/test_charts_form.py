"""Tests for ChartParamsForm."""
from __future__ import annotations

from admin_extended.charts.forms import ChartParamsForm
from admin_extended.charts.models import Aggregate, Scale, TimeRange, TimeSeriesChart


def _chart(**kw) -> TimeSeriesChart:
    defaults = dict(
        name="t", target_app_label="sample_app", target_model_name="Order",
        time_field="created_at", aggregate=Aggregate.COUNT, aggregate_field="*",
        aggregate_label="orders",
    )
    defaults.update(kw)
    return TimeSeriesChart.objects.create(**defaults)


def test_form_without_filter_field_omits_filter_value(db):
    chart = _chart()
    form = ChartParamsForm({"time_range": "7", "scale": Scale.DAY}, chart=chart)
    assert "filter_value" not in form.fields


def test_form_with_filter_field_offers_choices(db):
    chart = _chart(filter_field="region")
    form = ChartParamsForm({"time_range": "7", "scale": Scale.DAY}, chart=chart)
    assert "filter_value" in form.fields
    assert form.fields["filter_value"].choices[0] == ("", "All")


def test_form_time_range_coerced_to_int(db):
    chart = _chart()
    form = ChartParamsForm({"time_range": "7", "scale": Scale.DAY}, chart=chart)
    assert form.is_valid(), form.errors
    assert form.cleaned_data["time_range"] == 7
    assert form.cleaned_data["time_range"] == TimeRange.LAST_7_DAY


def test_form_rejects_invalid_scale(db):
    chart = _chart()
    form = ChartParamsForm({"time_range": "7", "scale": "DECADE"}, chart=chart)
    assert not form.is_valid()
    assert "scale" in form.errors

"""Tests for TimeSeriesChart.clean() validation."""
from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError

from admin_extended.charts.models import Aggregate, TimeSeriesChart


def _make(**kw) -> TimeSeriesChart:
    defaults = dict(
        name="t",
        target_app_label="sample_app",
        target_model_name="Order",
        time_field="created_at",
        aggregate=Aggregate.COUNT,
        aggregate_field="*",
        aggregate_label="orders",
    )
    defaults.update(kw)
    return TimeSeriesChart(**defaults)


def test_clean_accepts_valid_count_chart(db):
    _make().clean()  # no raise


def test_clean_rejects_unknown_model(db):
    with pytest.raises(ValidationError, match="target_model_name"):
        _make(target_model_name="DoesNotExist").clean()


def test_clean_rejects_unknown_time_field(db):
    with pytest.raises(ValidationError, match="time_field"):
        _make(time_field="missing_at").clean()


def test_clean_requires_specific_field_for_sum(db):
    with pytest.raises(ValidationError, match="aggregate_field"):
        _make(aggregate=Aggregate.SUM, aggregate_field="*").clean()


def test_clean_accepts_sum_with_valid_field(db):
    _make(aggregate=Aggregate.SUM, aggregate_field="quantity").clean()


def test_clean_rejects_split_field_not_on_model(db):
    with pytest.raises(ValidationError, match="split_field"):
        _make(split_field="missing").clean()


def test_clean_rejects_malformed_filters(db):
    with pytest.raises(ValidationError, match="filters"):
        _make(filters="not a query string").clean()

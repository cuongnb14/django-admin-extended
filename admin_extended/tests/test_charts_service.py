"""Tests for ChartQueryService — pure query logic."""
from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from admin_extended.charts.models import Aggregate, Scale, TimeRange, TimeSeriesChart
from admin_extended.charts.services import ChartParams, ChartQueryService, ChartResult
from admin_extended.tests.example_project.sample_app.models import Customer, Order, Product


@pytest.fixture
def chart(db) -> TimeSeriesChart:
    return TimeSeriesChart.objects.create(
        name="orders-by-day",
        target_app_label="sample_app",
        target_model_name="Order",
        time_field="created_at",
        aggregate=Aggregate.COUNT,
        aggregate_field="*",
        aggregate_label="orders",
    )


@pytest.fixture
def seeded(db):
    customer = Customer.objects.create(name="C", email="c@c.com")
    product = Product.objects.create(name="P", price=1)
    now = timezone.now()
    for offset in (0, 1, 2):
        for _ in range(2 + offset):
            o = Order.objects.create(customer=customer, product=product, quantity=1)
            Order.objects.filter(pk=o.pk).update(created_at=now - timedelta(days=offset))
    return customer, product


def test_run_returns_chart_result(chart, seeded):
    result = chart  # noqa: F841 — fixture used
    svc = ChartQueryService(chart)
    params = ChartParams(time_range=TimeRange.LAST_7_DAY, scale=Scale.DAY, filter_value=None)
    out = svc.run(params)
    assert isinstance(out, ChartResult)
    assert out.chart_type == chart.chart_type
    assert len(out.labels) >= 1
    assert len(out.datasets) == 1
    assert out.datasets[0].label == "orders"


def test_run_caps_to_max_points(chart, seeded):
    chart.max_points = 1
    chart.save()
    svc = ChartQueryService(chart)
    params = ChartParams(time_range=TimeRange.ALL_TIME, scale=Scale.DAY, filter_value=None)
    out = svc.run(params)
    assert len(out.labels) <= 1

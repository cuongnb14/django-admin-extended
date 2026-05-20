"""Tests for chart views."""
from __future__ import annotations

from django.urls import reverse

from admin_extended.charts.models import Aggregate, TimeSeriesChart


def _chart(**kw) -> TimeSeriesChart:
    defaults = dict(
        name="t", target_app_label="sample_app", target_model_name="Order",
        time_field="created_at", aggregate=Aggregate.COUNT, aggregate_field="*",
        aggregate_label="orders",
    )
    defaults.update(kw)
    return TimeSeriesChart.objects.create(**defaults)


def test_metrics_view_returns_json(admin_client, db):
    chart = _chart()
    url = reverse("admin:admin_extended_charts_metrics", args=[chart.pk])
    response = admin_client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert "labels" in data and "datasets" in data


def test_metrics_view_rejects_invalid_scale(admin_client, db):
    chart = _chart()
    url = reverse("admin:admin_extended_charts_metrics", args=[chart.pk])
    response = admin_client.get(url, {"scale": "DECADE"})
    assert response.status_code == 400


def test_metrics_view_requires_staff(client, db):
    chart = _chart()
    url = reverse("admin:admin_extended_charts_metrics", args=[chart.pk])
    response = client.get(url)
    # admin_view redirects to login
    assert response.status_code in (302, 403)


def test_chart_view_renders_html(admin_client, db):
    chart = _chart()
    url = reverse("admin:admin_extended_charts_chart", args=[chart.pk])
    response = admin_client.get(url)
    assert response.status_code == 200

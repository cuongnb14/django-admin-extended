"""URL patterns for chart views, mounted by ChartAdmin.get_urls."""
from __future__ import annotations

from django.urls import path

from .views import ChartView, MetricsView

urlpatterns = [
    path("<int:chart_id>/chart/", ChartView.as_view(), name="admin_extended_charts_chart"),
    path("<int:chart_id>/metrics/", MetricsView.as_view(), name="admin_extended_charts_metrics"),
]

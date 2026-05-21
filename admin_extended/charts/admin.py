"""TimeSeriesChartAdmin — thin layer that mounts the chart URLs."""
from __future__ import annotations

from django.contrib import admin
from django.urls import reverse

from ..core import ExtendedModelAdmin
from ..display import html_link
from .models import TimeSeriesChart


@admin.register(TimeSeriesChart)
class TimeSeriesChartAdmin(ExtendedModelAdmin):
    list_display = ("name", "chart_type", "target_app_label", "target_model_name", "chart_link")
    list_display_links = ("name",)
    search_fields = ("name",)

    fieldsets = (
        (None, {"fields": ("name", "description", ("chart_type", "stacked"))}),
        ("Target model", {"fields": (
            ("target_app_label", "target_model_name", "time_field"),
            ("aggregate", "aggregate_field", "aggregate_label"),
            ("split_field", "filter_field", "filters"),
        )}),
        ("Time options", {"fields": ("default_time_range", "default_scale")}),
        ("Performance", {"fields": (("max_points", "cache_seconds"),)}),
    )

    def get_urls(self):  # type: ignore[no-untyped-def]
        from django.urls import path
        from .views import ChartView, MetricsView
        admin_view = self.admin_site.admin_view
        custom_urls = [
            path("<int:chart_id>/chart/", admin_view(ChartView.as_view()), name="admin_extended_charts_chart"),
            path("<int:chart_id>/metrics/", admin_view(MetricsView.as_view()), name="admin_extended_charts_metrics"),
        ]
        return custom_urls + super().get_urls()

    @admin.display(description="Chart")
    def chart_link(self, obj: TimeSeriesChart):
        return html_link(reverse("admin:admin_extended_charts_chart", args=[obj.pk]), title="View chart")

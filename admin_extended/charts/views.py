"""MetricsView (JSON) and ChartView (HTML) for TimeSeriesChart."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from django.contrib import admin
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.generic import View

from .forms import ChartParamsForm
from .models import TimeSeriesChart
from .services import ChartParams, ChartQueryService


class _BaseChartView(View):
    chart: TimeSeriesChart

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:  # type: ignore[override]
        self.chart = get_object_or_404(TimeSeriesChart, pk=kwargs["chart_id"])
        return super().dispatch(request, *args, **kwargs)

    def _resolve_params(self, request: HttpRequest) -> ChartParams | HttpResponse:
        data = {
            "time_range": str(self.chart.default_time_range),
            "scale": self.chart.default_scale,
        }
        data.update(request.GET.dict())
        form = ChartParamsForm(data, chart=self.chart)
        if not form.is_valid():
            return JsonResponse({"errors": form.errors}, status=400)
        cd = form.cleaned_data
        return ChartParams(
            time_range=cd["time_range"],
            scale=cd["scale"],
            filter_value=cd.get("filter_value") or None,
        )


class MetricsView(_BaseChartView):
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        params = self._resolve_params(request)
        if isinstance(params, HttpResponse):
            return params
        result = ChartQueryService(self.chart).run_cached(params)
        payload = {
            "chart_type": result.chart_type,
            "stacked": result.stacked,
            "labels": result.labels,
            "datasets": [asdict(s) for s in result.datasets],
        }
        return JsonResponse(payload)


class ChartView(_BaseChartView):
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        chart = self.chart
        form = ChartParamsForm(request.GET or None, chart=chart)
        context = {
            **admin.site.each_context(request),
            "chart": chart,
            "chart_title": chart.name,
            "form": form,
            "metrics_url": reverse("admin:admin_extended_charts_metrics", args=[chart.pk]),
        }
        return TemplateResponse(request, "admin/admin_extended/charts/chart.html", context)

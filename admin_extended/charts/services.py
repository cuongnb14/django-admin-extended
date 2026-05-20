"""Pure query layer for TimeSeriesChart — no HTTP, no JSON."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import timedelta
from typing import Any
from urllib.parse import parse_qsl

from django.core.cache import cache
from django.db.models import F
from django.utils import timezone

from .models import Scale, TimeRange, TimeSeriesChart, trunc_for


@dataclass(frozen=True, slots=True)
class ChartParams:
    time_range: int
    scale: str
    filter_value: str | None = None


@dataclass(frozen=True, slots=True)
class ChartSeries:
    label: str
    data: list[float]


@dataclass(frozen=True, slots=True)
class ChartResult:
    chart_type: str
    stacked: bool
    labels: list[str]
    datasets: list[ChartSeries]


class ChartQueryService:
    def __init__(self, chart: TimeSeriesChart) -> None:
        self.chart = chart

    # ---- filter choices (cached 5min) ---------------------------------

    def filter_choices(self) -> list[tuple[str, str]]:
        chart = self.chart
        if not chart.filter_field:
            return []
        key = f"admin_extended_charts:filter_choices:{chart.pk}"
        cached = cache.get(key)
        if cached is not None:
            return cached
        target = chart.get_target_model()
        values = list(target.objects.values_list(chart.filter_field, flat=True).distinct())
        choices = [(str(v), str(v)) for v in values if v is not None]
        cache.set(key, choices, 300)
        return choices

    # ---- run / run_cached --------------------------------------------

    def run(self, params: ChartParams) -> ChartResult:
        chart = self.chart
        target = chart.get_target_model()
        bucket = trunc_for(params.scale)(chart.time_field)

        filters: dict[str, Any] = dict(parse_qsl(chart.filters or ""))
        if params.filter_value and chart.filter_field:
            filters[chart.filter_field] = params.filter_value
        if params.time_range:
            filters[f"{chart.time_field}__gte"] = timezone.now() - timedelta(days=params.time_range)

        qs = target.objects.filter(**filters).annotate(time=bucket)
        values_kwargs: dict[str, Any] = {}
        if chart.split_field:
            values_kwargs["split"] = F(chart.split_field)
            qs = qs.values("time", **values_kwargs)
        else:
            qs = qs.values("time")
        qs = qs.annotate(total=chart.get_aggregate()).order_by("time")[: chart.max_points]

        rows = list(qs)
        return self._shape(rows, params.scale)

    def run_cached(self, params: ChartParams) -> ChartResult:
        if self.chart.cache_seconds <= 0:
            return self.run(params)
        key = f"admin_extended_charts:result:{self.chart.pk}:{hash(params)}"
        cached = cache.get(key)
        if cached is not None:
            return cached
        result = self.run(params)
        cache.set(key, result, self.chart.cache_seconds)
        return result

    # ---- shaping ------------------------------------------------------

    def _date_format(self, scale: str) -> str:
        return "%Y-%m-%d %H:%M" if scale == Scale.HOUR else "%Y-%m-%d"

    def _shape(self, rows: list[dict[str, Any]], scale: str) -> ChartResult:
        chart = self.chart
        date_fmt = self._date_format(scale)

        if not chart.split_field:
            labels = [row["time"].strftime(date_fmt) for row in rows]
            data = [float(row["total"] or 0) for row in rows]
            datasets = [ChartSeries(label=chart.aggregate_label, data=data)]
        else:
            labels: list[str] = []
            seen: set[str] = set()
            by_split: dict[str, dict[str, float]] = defaultdict(dict)
            for row in rows:
                label = row["time"].strftime(date_fmt)
                if label not in seen:
                    labels.append(label)
                    seen.add(label)
                by_split[row["split"]][label] = float(row["total"] or 0)
            datasets = [
                ChartSeries(label=str(k), data=[by_split[k].get(label, 0.0) for label in labels])
                for k in by_split
            ]

        return ChartResult(
            chart_type=chart.chart_type,
            stacked=chart.stacked,
            labels=labels,
            datasets=datasets,
        )

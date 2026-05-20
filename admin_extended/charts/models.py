"""TimeSeriesChart model + enums + Scale -> Trunc mapping (single source of truth)."""
from __future__ import annotations

from typing import Any

from django.apps import apps as django_apps
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import TruncDay, TruncHour, TruncMonth, TruncWeek


class Aggregate(models.TextChoices):
    COUNT = "COUNT", "COUNT"
    SUM = "SUM", "SUM"
    AVG = "AVG", "AVG"
    MIN = "MIN", "MIN"
    MAX = "MAX", "MAX"


class TimeRange(models.IntegerChoices):
    LAST_7_DAY = 7, "Last 7 days"
    LAST_30_DAY = 30, "Last 30 days"
    LAST_YEAR = 365, "Last 1 year"
    ALL_TIME = 0, "All time"


class Scale(models.TextChoices):
    HOUR = "HOUR", "Hour"
    DAY = "DAY", "Day"
    WEEK = "WEEK", "Week"
    MONTH = "MONTH", "Month"


class ChartType(models.TextChoices):
    BAR = "BAR", "Bar"
    LINE = "LINE", "Line"


_TRUNC_FOR_SCALE: dict[str, type] = {
    Scale.HOUR: TruncHour,
    Scale.DAY: TruncDay,
    Scale.WEEK: TruncWeek,
    Scale.MONTH: TruncMonth,
}


def trunc_for(scale: str) -> type:
    return _TRUNC_FOR_SCALE[scale]


class TimeSeriesChart(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=1000, null=True, blank=True, default=None)
    chart_type = models.CharField(max_length=55, choices=ChartType.choices, default=ChartType.BAR)
    stacked = models.BooleanField(default=False)

    default_time_range = models.IntegerField(choices=TimeRange.choices, default=TimeRange.LAST_30_DAY)
    default_scale = models.CharField(max_length=45, choices=Scale.choices, default=Scale.DAY)

    target_app_label = models.CharField(max_length=255)
    target_model_name = models.CharField(max_length=255)
    time_field = models.CharField(max_length=255)
    aggregate = models.CharField(max_length=45, choices=Aggregate.choices)
    aggregate_field = models.CharField(max_length=255, default="*")
    aggregate_label = models.CharField(max_length=255)

    split_field = models.CharField(max_length=255, null=True, blank=True, default=None)
    filter_field = models.CharField(max_length=255, null=True, blank=True, default=None)
    filters = models.CharField(
        max_length=1000, null=True, blank=True, default=None,
        help_text="Filters for query. Example: status=1&cate=3",
    )

    max_points = models.PositiveIntegerField(default=1000)
    cache_seconds = models.PositiveIntegerField(default=0, help_text="0 = no cache")

    def __str__(self) -> str:
        return self.name

    # ---- helpers --------------------------------------------------------

    def get_target_model(self) -> type[models.Model]:
        return django_apps.get_model(app_label=self.target_app_label, model_name=self.target_model_name)

    def get_aggregate(self) -> Any:
        return {
            Aggregate.COUNT: models.Count,
            Aggregate.SUM: models.Sum,
            Aggregate.AVG: models.Avg,
            Aggregate.MIN: models.Min,
            Aggregate.MAX: models.Max,
        }[self.aggregate](self.aggregate_field)

    # ---- validation ----------------------------------------------------

    def clean(self) -> None:
        try:
            target = self.get_target_model()
        except LookupError as err:
            raise ValidationError({"target_model_name": "Target model does not exist"}) from err

        field_names = {f.name for f in target._meta.fields}

        if self.time_field not in field_names:
            raise ValidationError({"time_field": f"'{self.time_field}' is not a field of {target.__name__}"})

        if self.aggregate != Aggregate.COUNT and self.aggregate_field == "*":
            raise ValidationError({"aggregate_field": f"{self.aggregate} requires a specific field"})

        if self.aggregate_field != "*" and self.aggregate_field not in field_names:
            raise ValidationError({"aggregate_field": f"'{self.aggregate_field}' is not a field of {target.__name__}"})

        if self.split_field and self.split_field not in field_names:
            raise ValidationError({"split_field": f"'{self.split_field}' is not a field of {target.__name__}"})

        if self.filter_field and self.filter_field not in field_names:
            raise ValidationError({"filter_field": f"'{self.filter_field}' is not a field of {target.__name__}"})

        if self.filters:
            try:
                from urllib.parse import parse_qsl
                parse_qsl(self.filters, keep_blank_values=False, strict_parsing=True)
            except ValueError as err:
                raise ValidationError({"filters": "Could not parse as query string"}) from err

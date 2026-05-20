"""ChartParamsForm — single form for both metrics and chart views."""
from __future__ import annotations

from django import forms

from .models import Scale, TimeRange, TimeSeriesChart
from .services import ChartQueryService


class ChartParamsForm(forms.Form):
    time_range = forms.TypedChoiceField(choices=TimeRange.choices, coerce=int)
    scale = forms.ChoiceField(choices=Scale.choices)
    filter_value = forms.ChoiceField(required=False)

    def __init__(self, *args, chart: TimeSeriesChart, **kwargs):  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        if chart.filter_field:
            choices = ChartQueryService(chart).filter_choices()
            self.fields["filter_value"].choices = [("", "All"), *choices]
            self.fields["filter_value"].label = chart.filter_field.replace("_", " ").title()
        else:
            self.fields.pop("filter_value")

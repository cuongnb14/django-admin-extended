from collections import defaultdict
from datetime import timedelta

from django import forms
from django.contrib import admin
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncHour
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import path
from django.utils import timezone
from django.utils.html import format_html

from ..models import TimeSeriesChart

SCALE_MAPPING = {
    'HOUR': TruncHour,
    'DAY': TruncDay,
    'WEEK': TruncWeek,
    'MONTH': TruncMonth,
}


class ChartStandardForm(forms.Form):
    time_range = forms.CharField(widget=forms.Select(choices=TimeSeriesChart.TimeRange.choices), required=False)
    scale = forms.CharField(widget=forms.Select(choices=TimeSeriesChart.Scale.choices), required=False)


class ChartFilterForm(forms.Form):
    time_range = forms.CharField(widget=forms.Select(choices=TimeSeriesChart.TimeRange.choices), required=False)
    scale = forms.CharField(widget=forms.Select(choices=TimeSeriesChart.Scale.choices), required=False)
    filters = forms.ChoiceField(required=False)


@admin.register(TimeSeriesChart)
class TimeSeriesChartAdmin(admin.ModelAdmin):
    list_display = ('display_chart_url', 'name', 'chart_type', 'app_label', 'model_name')
    list_display_links = ('name',)
    search_fields = ('name',)
    fieldsets = (
        (
            None,
            {
                'fields': (
                    'name', 'description',
                    ('chart_type', 'stacked')
                )
            },
        ),
        (
            'Target model',
            {
                'fields': (
                    ('app_label', 'model_name', 'time_field'),
                    ('aggregate', 'aggregate_field', 'aggregate_label'),
                    ('split_field', 'filter_field', 'filters')
                )
            }
        ),
        (
            'Time options',
            {
                'fields': (
                    'default_time_range',
                    'default_scale',
                )
            }
        ),
    )

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('<int:chart_id>/chart/', self.admin_site.admin_view(self.chart_view), name='admin_chart_chart'),
            path('<int:chart_id>/metrics/', self.admin_site.admin_view(self.metrics_api), name='admin_chart_metrics'),
        ]
        return my_urls + urls

    def metrics_api(self, request, chart_id):
        chart = TimeSeriesChart.objects.get(id=chart_id)
        data = {
            'time_range': request.GET.get('time_range', chart.default_time_range),
            'scale': request.GET.get('scale', chart.default_scale),
            'filters': request.GET.get('filters', None)
        }

        if chart.filter_field:
            form = ChartFilterForm(data)
            StatsModel = chart.get_stats_model()
            choices = StatsModel.objects.values_list(chart.filter_field, flat=True).distinct()
            choices = [(x, x) for x in choices]
            form.fields['filters'].choices = choices
        else:
            form = ChartStandardForm(data)

        if form.is_valid():
            time_range = int(form.cleaned_data.get('time_range'))
            scale = form.cleaned_data.get('scale')
            filter_value = form.cleaned_data.get('filters', None)
        else:
            raise Exception('filter is invalid')

        if scale == TimeSeriesChart.Scale.HOUR:
            date_format = '%Y-%m-%d %H:%M'
        else:
            date_format = '%Y-%m-%d'

        if time_range:
            start_time = timezone.now() - timedelta(days=time_range)
        else:
            start_time = None
        stats = chart.get_queryset(start_time, scale, filter_value)

        labels = []

        if not chart.split_field:
            data = []
            for item in stats:
                labels.append(item['time'].strftime(date_format))
                data.append(str(item['total'] if item['total'] is not None else 0))
            datasets = [
                {
                    'label': chart.aggregate_label,
                    'data': data
                }
            ]
        else:
            labels = []
            last_labels = None
            data = defaultdict(dict)
            for item in stats:
                label = item['time'].strftime(date_format)
                if item['time'] != last_labels:
                    labels.append(label)
                    last_labels = item['time']
                data[item['split']][label] = item['total']

            split_names = data.keys()
            datasets = defaultdict(list)

            for label in labels:
                for name in split_names:
                    datasets[name].append(data[name].get(label, 0))

            datasets = [{'label': k, 'data': v} for k, v in datasets.items()]

        return JsonResponse({
            'chart_type': chart.chart_type,
            'stacked': chart.stacked,
            'labels': labels,
            'datasets': datasets
        })

    def chart_view(self, request, chart_id):
        context = {
            **admin.site.each_context(request),
        }

        chart = TimeSeriesChart.objects.get(id=chart_id)

        data = {
            'time_range': request.GET.get('time_range', chart.default_time_range),
            'scale': request.GET.get('scale', chart.default_scale),
        }

        if chart.filter_field:
            form = ChartFilterForm(data)
            StatsModel = chart.get_stats_model()
            choices = StatsModel.objects.values_list(chart.filter_field, flat=True).distinct()
            choices = [(x, x) for x in choices]
            choices = [('', 'All')] + choices
            form.fields['filters'].choices = choices
            form.fields['filters'].label = chart.filter_field.title()
        else:
            form = ChartStandardForm(data)

        context["chart"] = chart
        context["chart_title"] = chart.name
        context["form"] = form

        return render(request, 'admin/chart.html', context)

    @admin.display(description='View Chart')
    def display_chart_url(self, obj):
        return format_html('<a href="/admin/admin_extended/timeserieschart/{}/chart/">View Chart</a>', obj.id)

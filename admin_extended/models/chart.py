from django.apps import apps
from django.db import models
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncHour


SCALE_MAPPING = {
    'HOUR': TruncHour,
    'DAY': TruncDay,
    'WEEK': TruncWeek,
    'MONTH': TruncMonth,
}


class TimeSeriesChart(models.Model):
    class Aggregate(models.TextChoices):
        COUNT = 'COUNT', 'COUNT'
        SUM = 'SUM', 'SUM'
        AVG = 'AVG', 'AVG'
        MIN = 'MIN', 'MIN'
        MAX = 'MAX', 'MAX'

    class TimeRange(models.IntegerChoices):
        LAST_7_DAY = '7', 'Last 7 days'
        LAST_30_DAY = '30', 'Last 30 days'
        LAST_YEAR = '365', 'Last 1 year'
        ALL_TIME = '0', 'All time'

    class Scale(models.TextChoices):
        HOUR = 'HOUR', 'Hour'
        DAY = 'DAY', 'Day'
        WEEK = 'WEEK', 'Week'
        MONTH = 'MONTH', 'Month'

    class ChartType(models.TextChoices):
        BAR = 'BAR', 'Bar'
        LINE = 'LINE', 'Line'

    name = models.CharField(max_length=255)
    description = models.CharField(max_length=1000, null=True, blank=True, default=None)
    chart_type = models.CharField(max_length=55, choices=ChartType.choices, default=ChartType.BAR)
    stacked = models.BooleanField(default=False)

    default_time_range = models.IntegerField(choices=TimeRange.choices, default=TimeRange.LAST_30_DAY)
    default_scale = models.CharField(max_length=45, choices=Scale.choices, default=Scale.DAY)

    app_label = models.CharField(max_length=255)
    model_name = models.CharField(max_length=255)
    time_field = models.CharField(max_length=255)
    aggregate = models.CharField(max_length=45, choices=Aggregate.choices)
    aggregate_field = models.CharField(max_length=255, default='*')
    aggregate_label = models.CharField(max_length=255)

    split_field = models.CharField(max_length=255, null=True, blank=True, default=None)
    filter_field = models.CharField(max_length=255, null=True, blank=True, default=None)
    filters = models.CharField(max_length=1000, null=True, blank=True, default=None,
                               help_text='Filters for query. Example value: status=1&cate=3')

    def __str__(self):
        return self.name

    def get_aggregate(self):
        mapping = {
            self.Aggregate.COUNT: models.Count,
            self.Aggregate.SUM: models.Sum,
            self.Aggregate.AVG: models.Avg,
            self.Aggregate.MIN: models.Min,
            self.Aggregate.MAX: models.Max,
        }
        return mapping[self.aggregate](self.aggregate_field)

    def parse_filters(self):
        results = {}
        if self.filters:
            filters = self.filters.split('&')
            for item in filters:
                key, value = item.split('=')
                results[key] = value
        return results

    def get_stats_model(self):
        return apps.get_model(app_label=self.app_label, model_name=self.model_name)

    def get_queryset(self, start_time, scale, filter_value=None):
        StatsModel = self.get_stats_model()

        values = {}
        if self.split_field:
            values['split'] = models.F(self.split_field)
        filters = self.parse_filters()
        if filter_value:
            filters[self.filter_field] = filter_value

        if start_time:
            filters[f'{self.time_field}__gte'] = start_time

        return StatsModel.objects.filter(**filters) \
            .annotate(time=SCALE_MAPPING[scale](self.time_field)) \
            .values('time', **values) \
            .annotate(total=self.get_aggregate()).order_by('time')

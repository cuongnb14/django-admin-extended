from dataclasses import dataclass

from django.contrib import admin
from django.shortcuts import render
from django.urls import path


@dataclass
class TableData:
    header: str
    table_titles = []
    table_rows = []

    def add_rows(self, row: list):
        self.table_rows.append(row)


class CustomTableAdminPage(admin.ModelAdmin):
    model = None

    def get_urls(self):
        view_name = '{}_{}_changelist'.format(self.model._meta.app_label, self.model._meta.model_name)
        return [
            path('', self.custom_view, name=view_name),
        ]

    def get_table_data(self):
        """
        return list of TableData
        """
        raise NotImplementedError()

    def custom_view(self, request, *args, **kwargs):
        context = {
            **admin.site.each_context(request),
            'tables': self.get_table_data(),
        }

        return render(request, 'admin/custom/custom_table_page.html', context)

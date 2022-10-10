import copy
import json

from django.contrib import admin
from django.shortcuts import render
from django.urls import path
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .settings import ADMIN_EXTENDED_SETTINGS


class ExtendedAdminModel(admin.ModelAdmin):

    TEXT_COLOR_SUCCESS = 'green'
    TEXT_COLOR_ERROR = 'red'
    TEXT_COLOR_WARNING = 'orange'

    ext_read_only_fields = []
    ext_write_only_fields = []

    tab_inline = None
    delete_without_confirm = False

    @admin.action(description='Delete selected without confirm')
    def action_delete_without_confirm(self, request, queryset):
        result = queryset.delete()
        messages.success(request, f'Deleted {result[0]} record')

    def get_actions(self, request):
        actions = super().get_actions(request)
        if self.delete_without_confirm:
            if 'delete_selected' in actions:
                del actions['delete_selected']
            actions['action_delete_without_confirm'] = self.get_action('action_delete_without_confirm')
        return actions


    def _changeform_view(self, request, object_id, form_url, extra_context):
        request.page_type = self.get_page_type(request, object_id)
        return super()._changeform_view(request, object_id, form_url, extra_context)

    def get_page_type(self, request, obj=None):
        if obj:
            if 'edit' not in request.GET and '_popup' not in request.GET:
                return 'view'
            else:
                return 'edit'
        else:
            return 'add'

    def has_change_permission(self, request, obj=None):
        page_type = self.get_page_type(request, obj)
        if page_type == 'view':
            return False
        return super().has_change_permission(request, obj)

    def get_fieldsets(self, request, obj=None):
        fieldsets = copy.deepcopy(super().get_fieldsets(request, obj))
        if request.page_type == 'view':
            if self.ext_write_only_fields:
                for fieldset in fieldsets:
                    fields = []
                    for f in fieldset[1]['fields']:
                        if f not in self.ext_write_only_fields:
                            fields.append(f)
                    fieldset[1]['fields'] = fields

        else:
            if self.ext_read_only_fields:
                for fieldset in fieldsets:
                    fields = []
                    for f in fieldset[1]['fields']:
                        if f not in self.ext_read_only_fields:
                            fields.append(f)
                    fieldset[1]['fields'] = fields

        return fieldsets

    def get_html_img_tag(self, url, height='200px'):
        return format_html('<img height="{}" src="{}" />', height, url)

    def get_html_a_tag(self, url, title=None, target='_blank', html_class=''):
        title = title if title else url
        return format_html(
            '<a href="{}" class="{}" target="{}">{}</a>',
            url, html_class, target, title
        )

    def get_html_text_color(self, title, color):
        return format_html('<b style="color:{};">{}</b>', color, title)

    def format_json(self, content, indent=4):
        content = json.dumps(content, indent=indent)
        return format_html('<pre>{}</pre>', content)

    def get_inline_instances(self, request, obj=None):
        inline_instances = super().get_inline_instances(request, obj)

        request.is_tabbed = False
        if inline_instances:
            if ADMIN_EXTENDED_SETTINGS['MODEL_ADMIN_TABBED_INLINE'] or self.tab_inline:
                request.is_tabbed = True

        return inline_instances


class CustomTableAdminPage(admin.ModelAdmin):
    model = None

    def get_urls(self):
        view_name = '{}_{}_changelist'.format(self.model._meta.app_label, self.model._meta.model_name)
        return [
            path('', self.custom_view, name=view_name),
        ]

    def get_data(self):
        """
        return dict of list. Eg:
        results = {
            'title': ['A', 'B', 'C'],
            'rows': [
                [12, 12, 14],
                [12, 12, 14],
                [12, 12, 14],
                [12, 12, 14],
            ],
        }
        """
        raise NotImplementedError()

    def custom_view(self, request, *args, **kwargs):
        context = {
            **admin.site.each_context(request),
            'data': self.get_data(),
        }

        return render(request, 'admin/custom/custom_table_page.html', context)

import copy
import json

from django.contrib import admin
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

        elif request.page_type == 'edit':
            if self.ext_read_only_fields:
                for fieldset in fieldsets:
                    fields = []
                    for f in fieldset[1]['fields']:
                        if f not in self.ext_read_only_fields:
                            fields.append(f)
                    fieldset[1]['fields'] = fields

        return fieldsets

    def get_html_img_tag(self, url, height='200px'):
        return format_html(f'<img height="{height}" src="{url}" />')

    def get_html_a_tag(self, url, title=None, target='_blank', html_class=''):
        title = title if title else url
        return format_html(f'<a href="{url}" class="{html_class}" target="{target}">{title}</a>')

    def get_html_text_color(self, title, color):
        return format_html(f'<b style="color:{color};">{title}</b>')

    def format_json(self, content, indent=4):
        content = json.dumps(content, indent=indent)
        return mark_safe(f'<pre>{content}</pre>')

    def get_inline_instances(self, request, obj=None):
        inline_instances = super().get_inline_instances(request, obj)

        request.is_tabbed = False
        if inline_instances:
            if ADMIN_EXTENDED_SETTINGS['MODEL_ADMIN_TABBED_INLINE'] or self.tab_inline:
                request.is_tabbed = True

        return inline_instances

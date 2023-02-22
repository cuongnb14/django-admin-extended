import copy
import json

from django.contrib import messages
from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path, reverse
from django.db.models import ForeignKey, OneToOneField
from django.utils.html import format_html

from .settings import ADMIN_EXTENDED_SETTINGS


class ChangeFormAction:
    action_name = None
    param_name = None
    param_title = None
    btn_color = None

    def handle(self, request):
        raise NotImplementedError


class ChangeFormActionAdminModelMixin:
    change_form_action_classes = []
    change_form_object_tools = []

    def get_urls(self):
        urls = super().get_urls()
        opts = self.model._meta
        action_url_name = '{}_{}_action'.format(opts.app_label, opts.model_name)
        custom_urls = [
            path('action/', self.admin_site.admin_view(self.change_from_action_view), name=action_url_name),
        ]
        return custom_urls + urls

    def get_change_form_actions(self, request, object_id):
        return [x() for x in self.change_form_action_classes]

    def get_change_form_object_tools(self, request, object_id):
        return self.change_form_object_tools

    def change_from_action_view(self, request):
        if request.method == 'POST':
            action_name = request.POST.get('action_name')
            object_id = request.POST.get('object_id')

            change_form_action_registry = {x.action_name: x for x in self.get_change_form_actions(request, object_id)}
            action = change_form_action_registry.get(action_name)
            action.handle(request)
            opts = self.model._meta
            info = self.admin_site.name, opts.app_label, opts.model_name
            change_url_name = '{}:{}_{}_change'.format(*info)
            return redirect(change_url_name, object_id)

    def _changeform_view(self, request, object_id, form_url, extra_context):
        if object_id:
            change_form_actions = self.get_change_form_actions(request, object_id)
            opts = self.model._meta
            action_url_name = '{}:{}_{}_action'.format(self.admin_site.name, opts.app_label, opts.model_name)

            extra_context = extra_context if extra_context else {}
            extra_context['change_form_actions'] = change_form_actions
            extra_context['change_form_action_url'] = reverse(action_url_name)

            change_form_object_tools = self.get_change_form_object_tools(request, object_id)
            extra_context['change_form_object_tools'] = change_form_object_tools

        return super()._changeform_view(request, object_id, form_url, extra_context)


class ExtendedAdminModel(ChangeFormActionAdminModelMixin, admin.ModelAdmin):
    """
    Extend base model admin: tabbable inline model, separate view, edit model,...

    Attributes:
        :ext_read_only_fields Only show this fields in view modes
        :ext_write_only_fields  Only show this fields in edit modes
        :super_admin_only_fields Only show this fields for super admin
        :tab_inline tab inline or not
    """

    TEXT_COLOR_SUCCESS = 'green'
    TEXT_COLOR_ERROR = 'red'
    TEXT_COLOR_WARNING = 'orange'

    ext_read_only_fields = []
    ext_write_only_fields = []
    super_admin_only_fields = []

    tab_inline = ADMIN_EXTENDED_SETTINGS['MODEL_ADMIN_TABBED_INLINE']
    delete_without_confirm = False
    raw_id_fields_as_default = ADMIN_EXTENDED_SETTINGS['RAW_ID_FIELDS_AS_DEFAULT']

    def __init__(self, model, admin_site):
        if self.raw_id_fields_as_default:
            self.raw_id_fields = self.get_raw_id_fields(model)
        super().__init__(model, admin_site)

    def get_raw_id_fields(self, model):
        return tuple(
            f.name
            for f in model._meta.get_fields()
            if isinstance(f, ForeignKey) or isinstance(f, OneToOneField)
        )

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

    def filter_fieldsets(self, fieldsets, filter_func):
        for fieldset in fieldsets:
            fields = []
            for field in fieldset[1]['fields']:
                if type(field) is str:
                    if not filter_func(field):
                        fields.append(field)
                else:
                    list_fields = []
                    for item in field:
                        if not filter_func(item):
                            list_fields.append(item)
                    if list_fields:
                        fields.append(list_fields)
            fieldset[1]['fields'] = fields
        return fieldsets

    def filter_fieldsets_for_staff_user(self, request, fieldsets):
        if request.user.is_superuser:
            return fieldsets
        return self.filter_fieldsets(fieldsets, lambda x: x in self.super_admin_only_fields)

    def filter_fieldsets_for_page_type(self, page_type, fieldsets):
        """
        Filter ext_write_only_fields and ext_read_only_fields base on page type,
        also filter fields start with display_ from edit mode
        """

        if page_type == 'view':
            if self.ext_write_only_fields:
                fieldsets = self.filter_fieldsets(fieldsets, lambda x: x in self.ext_write_only_fields)
        else:
            fieldsets = self.filter_fieldsets(fieldsets, self.is_display_only_field)
        return fieldsets

    def get_fieldsets(self, request, obj=None):
        fieldsets = copy.deepcopy(super().get_fieldsets(request, obj))
        fieldsets = self.filter_fieldsets_for_page_type(page_type=request.page_type, fieldsets=fieldsets)
        fieldsets = self.filter_fieldsets_for_staff_user(request=request, fieldsets=fieldsets)
        return fieldsets

    def get_list_display(self, request):
        list_display = super().get_list_display(request)
        if request.user.is_superuser:
            return list_display
        return [x for x in list_display if x not in self.super_admin_only_fields]

    def is_display_only_field(self, field_name):
        return field_name in self.ext_read_only_fields or field_name.startswith('display_')

    def get_html_img_tag(self, url, height='200px'):
        if url:
            return format_html('<img height="{}" src="{}" />', height, url)
        return self.get_empty_value_display()

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
        request.is_tabbed = self.tab_inline
        return super().get_inline_instances(request, obj)


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

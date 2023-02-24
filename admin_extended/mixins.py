import json
from django.utils.html import format_html
from django.shortcuts import redirect
from django.urls import path, reverse

class UIUtilsMixin:
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


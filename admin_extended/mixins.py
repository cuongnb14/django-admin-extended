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
        return format_html('<a href="{}" class="{}" target="{}">{}</a>', url, html_class, target, title)

    def get_html_text_color(self, title, color):
        return format_html('<b style="color:{};">{}</b>', color, title)

    def format_json(self, content, indent=4):
        content = json.dumps(content, indent=indent)
        return format_html('<pre>{}</pre>', content)


class ObjectToolModelAdminMixin:
    change_form_object_tools = []
    change_list_object_tools = []

    def get_urls(self):
        urls = super().get_urls()

        base_url_name = "%s_%s" % (self.model._meta.app_label, self.model._meta.model_name)
        custom_urls = [
            path(
                '<int:object_id>/object-tools/<str:name>',
                self.admin_site.admin_view(self.change_form_object_tool_view),
                name=f'{base_url_name}_change_form_object_tool',
            ),
            path(
                'object-tools/<str:name>',
                self.admin_site.admin_view(self.change_list_object_tool_view),
                name=f'{base_url_name}_change_list_object_tool',
            ),
        ]
        return custom_urls + urls

    def get_change_form_object_tools(self, request):
        object_tools = []
        for change_form_object_tool in self.change_form_object_tools:
            object_tool = getattr(self, change_form_object_tool)
            object_tools.append(object_tool)
        return {object_tool.name: object_tool for object_tool in object_tools}

    def change_form_object_tool_view(self, request, object_id, name):
        change_form_object_tools = self.get_change_form_object_tools(request)
        return change_form_object_tools[name](request, object_id)

    def _get_render_change_form_object_tools(self, request, object_id):
        base_url_name = "%s_%s" % (self.model._meta.app_label, self.model._meta.model_name)
        change_form_object_tools = self.get_change_form_object_tools(request)
        object_tool_position = []
        submit_row_position = []

        for name, object_tool in change_form_object_tools.items():
            if object_tool.http_method == 'get':
                render_info = {
                    'icon': object_tool.icon,
                    'url': reverse(f'admin:{base_url_name}_change_form_object_tool', args=[object_id, name]),
                    'description': object_tool.description,
                }
                object_tool_position.append(render_info)

            else:
                submit_row_position.append(
                    {
                        'icon': object_tool.icon,
                        'url': reverse(f'admin:{base_url_name}_change_form_object_tool', args=[object_id, name]),
                        'description': object_tool.description,
                        'post_param_title': object_tool.post_param_title,
                    }
                )
        return object_tool_position, submit_row_position

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        if object_id:
            extra_context = extra_context if extra_context else {}
            object_tools = self._get_render_change_form_object_tools(request, object_id)
            extra_context['change_form_object_tools'] = object_tools[0]
            extra_context['change_form_submit_row'] = object_tools[1]

        return super().changeform_view(request, object_id, form_url, extra_context)

    def get_change_list_object_tools(self, request):
        object_tools = []
        for change_list_object_tool in self.change_list_object_tools:
            object_tool = getattr(self, change_list_object_tool)
            object_tools.append(object_tool)
        return {object_tool.name: object_tool for object_tool in object_tools}

    def change_list_object_tool_view(self, request, name):
        change_list_object_tools = self.get_change_list_object_tools(request)
        return change_list_object_tools[name](request)

    def _get_render_change_list_object_tools(self, request):
        base_url_name = "%s_%s" % (self.model._meta.app_label, self.model._meta.model_name)
        change_list_object_tools = self.get_change_list_object_tools(request)
        result = []
        for name, object_tool in change_list_object_tools.items():
            result.append(
                {
                    'icon': object_tool.icon,
                    'url': reverse(f'admin:{base_url_name}_change_list_object_tool', args=[name]),
                    'description': object_tool.description,
                }
            )
        return result

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context if extra_context else {}
        extra_context['change_list_object_tools'] = self._get_render_change_list_object_tools(request)

        return super().changelist_view(request, extra_context)

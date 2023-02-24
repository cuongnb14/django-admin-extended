from admin_extended.base import ExtendedAdminModel
from django.contrib import admin
from django.apps import apps

END_OF_LIST_DISPLAY = ['created_at', 'created', 'modified_at', 'modified']

def is_ignore_list_display_field(field):
    print(type(field).__name__)
    return field.name == 'id' or type(field).__name__ == 'TextField'

class DefaultModelAdmin(ExtendedAdminModel):
    def __init__(self, model, admin_site):
        list_display = ['__str__'] + [field.name for field in model._meta.fields if not is_ignore_list_display_field(field)]
        for item in END_OF_LIST_DISPLAY:
            if item in list_display:
                list_display.append(list_display.pop(list_display.index(item)))
        self.list_display = list_display
        
        self.list_filter = [field.name for field in model._meta.fields if field.choices]
        super().__init__(model, admin_site)

    def get_queryset(self, request):
        
        # Add related fields to select_related
        qs = super().get_queryset(request)
        related_fields = [field.name for field in self.model._meta.fields if field.is_relation]
        if related_fields:
            qs = qs.select_related(*related_fields)
        return qs


def auto_register_model_admin(default_model_admin_class=DefaultModelAdmin, ignore_models=[]):
    ignore_models = [x.lower() for x in ignore_models]
    all_models = apps.get_models()

    for model in all_models:
        try:
            model_identity = f'{model._meta.model_name}.{model._meta.app_label}'
            if not model.__module__.startswith('django') and model_identity not in ignore_models:
                admin.site.register(model, default_model_admin_class)
        except admin.sites.AlreadyRegistered:
            pass

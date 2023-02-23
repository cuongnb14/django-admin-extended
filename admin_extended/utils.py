from admin_extended.base import ExtendedAdminModel
from django.contrib import admin
from django.apps import apps


# Automatically Register All Models
class DefaultModelAdmin(ExtendedAdminModel):
    def __init__(self, model, admin_site):
        self.list_display = [field.name for field in model._meta.fields]
        super().__init__(model, admin_site)


def auto_register_model_admin(default_model_admin_class=DefaultModelAdmin, ignore_models=[]):
    all_models = apps.get_models()

    for model in all_models:
        try:
            model_identity = f'{model._meta.model_name}.{model._meta.app_label}'
            if not model.__module__.startswith('django') and model_identity not in ignore_models:
                admin.site.register(model, default_model_admin_class)
        except admin.sites.AlreadyRegistered:
            pass

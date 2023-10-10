from django.contrib import admin

def has_search_fields(field):
    model_admin = admin.site._registry.get(field.related_model)
    return model_admin and model_admin.search_fields

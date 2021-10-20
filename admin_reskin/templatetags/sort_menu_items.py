from django import template
from django.conf import settings

register = template.Library()

RESKIN_MENU_APP_ORDER = settings.RESKIN_MENU_APP_ORDER if hasattr(settings, 'RESKIN_MENU_APP_ORDER') else []
RESKIN_MENU_MODEL_ORDER = settings.RESKIN_MENU_MODEL_ORDER if hasattr(settings, 'RESKIN_MENU_MODEL_ORDER') else []
RESKIN_APP_ICON = settings.RESKIN_APP_ICON if hasattr(settings, 'RESKIN_APP_ICON') else {'user': 'fas fa-user', 'auth': 'fas fa-users',}


@register.filter
def sort_apps(apps):
    max_index = len(apps)
    for app in apps:
        if app['app_label'] == 'auth':
            app['name'] = 'Groups'
        if RESKIN_APP_ICON.get(app['app_label']):
            app['icon'] = RESKIN_APP_ICON.get(app['app_label'])
        else:
            app['icon'] = 'fas fa-layer-group'

    apps.sort(
        key=lambda x:
        RESKIN_MENU_APP_ORDER.index(x['app_label'])
        if x['app_label'] in RESKIN_MENU_APP_ORDER
        else max_index
    )
    return apps


@register.filter
def sort_models(models):
    max_index = len(models)
    models.sort(
        key=lambda x:
        RESKIN_MENU_MODEL_ORDER.index(x['object_name'])
        if x['object_name'] in RESKIN_MENU_MODEL_ORDER
        else max_index
    )
    return models

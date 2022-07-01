from django import template

from ..models import Bookmark
from ..settings import ADMIN_EXTENDED_SETTINGS

register = template.Library()

MENU_APP_ORDER = ADMIN_EXTENDED_SETTINGS['MENU_APP_ORDER']
MENU_MODEL_ORDER = ADMIN_EXTENDED_SETTINGS['MENU_MODEL_ORDER']
APP_ICON = ADMIN_EXTENDED_SETTINGS['APP_ICON']


@register.filter
def sort_apps(apps):
    max_index = len(apps)
    for app in apps:
        if app['app_label'] == 'auth':
            app['name'] = 'Groups'
        if APP_ICON.get(app['app_label']):
            app['icon'] = APP_ICON.get(app['app_label'])
        else:
            app['icon'] = 'fas fa-layer-group'

    apps.sort(
        key=lambda x:
        MENU_APP_ORDER.index(x['app_label'])
        if x['app_label'] in MENU_APP_ORDER
        else max_index
    )

    bookmarks = Bookmark.objects.filter(is_active=True).order_by('order')
    bookmarks_model = []
    for bookmark in bookmarks:
        item = {
            'name': bookmark.name,
            'object_name': bookmark.name,
            'perms': {'add': False, 'change': False, 'delete': False, 'view': True},
            'admin_url': bookmark.url,
            'view_only': True,
        }
        bookmarks_model.append(item)

    if bookmarks_model:
        bookmark_app = {
            'name': 'Bookmark',
            'icon': 'fas fa-bookmark',
            'app_label': 'admin_reskin_bookmark',
            'app_url': '/admin/admin_reskin/bookmark',
            'has_module_perms': True,
            'models': bookmarks_model,
        }

        apps = [bookmark_app] + apps

    return apps


@register.filter
def sort_models(models):
    max_index = len(models)
    models.sort(
        key=lambda x:
        MENU_MODEL_ORDER.index(x['object_name'])
        if x['object_name'] in MENU_MODEL_ORDER
        else max_index
    )
    return models

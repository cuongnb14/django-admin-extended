from django.conf import settings

ADMIN_EXTENDED_SETTINGS = {
    'MENU_APP_ORDER': [],
    'MENU_MODEL_ORDER': [],
    'APP_ICON': {},
    'MODEL_ADMIN_TABBED_INLINE': True,
}


user_settings = getattr(settings, "ADMIN_EXTENDED", {})

ADMIN_EXTENDED_SETTINGS.update(user_settings)

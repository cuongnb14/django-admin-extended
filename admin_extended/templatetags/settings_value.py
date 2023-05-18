from django import template
from django.conf import settings

register = template.Library()

@register.simple_tag
def settings_value(name, default=None):
    if '.' in name:
        keys = name.split('.')
        value = getattr(settings, keys[0], "")
        keys = keys[1:]
        for key in keys:
            if key not in value:
                return default
            value = value[key]
        return value
    return getattr(settings, name, default)

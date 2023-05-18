from django import template
from django.conf import settings

register = template.Library()

@register.simple_tag
def settings_value(name):
    if '.' in name:
        keys = name.split('.')
        value = getattr(settings, keys[0], "")
        keys = keys[1:]
        for key in keys:
            value = value[key]
        return value
    return getattr(settings, name, "")

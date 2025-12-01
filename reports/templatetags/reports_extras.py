# reports/templatetags/reports_extras.py
from django import template

register = template.Library()

@register.filter
def dict_get(d, key):
    """Return d[key] or None if not found."""
    if not d:
        return None
    return d.get(key)

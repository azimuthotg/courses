from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Allow dict[variable_key] lookup in Django templates."""
    return dictionary.get(key)

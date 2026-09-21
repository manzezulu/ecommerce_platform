# store/templatetags/store_extras.py
from django import template

register = template.Library()


@register.filter
def has_group(user, group_name):
    """Template filter: {{ user|has_group:"Vendors" }}

    Lets templates branch on group membership without needing the view
    to pass an extra boolean into every context.
    """
    if not user.is_authenticated:
        return False
    return user.groups.filter(name=group_name).exists()

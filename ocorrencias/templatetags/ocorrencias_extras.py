from django import template

register = template.Library()


@register.filter
def in_group(user, nome_grupo):
    """Uso no template: {% if user|in_group:"Administrador" %}"""
    if not user.is_authenticated:
        return False
    return user.groups.filter(name=nome_grupo).exists()

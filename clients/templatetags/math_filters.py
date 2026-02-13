from django import template

register = template.Library()


@register.filter
def mul(value, arg):
    """Умножение значения на аргумент."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def div(value, arg):
    """Деление значения на аргумент."""
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0

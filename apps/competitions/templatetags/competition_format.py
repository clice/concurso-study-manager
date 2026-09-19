from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def brl(value):
    if value in (None, ""):
        return "—"

    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return value

    integer, decimal = f"{amount:.2f}".split(".")
    groups = []
    while integer:
        groups.append(integer[-3:])
        integer = integer[:-3]

    return f"R$ {'.'.join(reversed(groups))},{decimal}"

"""
Custom template filters for payment calculations
"""

from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def mul(value, arg):
    """
    Multiply the value by the argument
    Usage: {{ price|mul:130 }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def to_kes(usd_amount, exchange_rate=130):
    """
    Convert USD to KES using exchange rate
    Usage: {{ price|to_kes }} or {{ price|to_kes:135 }}
    """
    try:
        return int(float(usd_amount) * float(exchange_rate))
    except (ValueError, TypeError):
        return 0

@register.filter
def format_currency(amount, currency='USD'):
    """
    Format currency with proper symbol
    Usage: {{ amount|format_currency:'KES' }}
    """
    try:
        amount = float(amount)
        if currency == 'KES':
            return f"KES {amount:,.0f}"
        elif currency == 'USD':
            return f"${amount:,.2f}"
        else:
            return f"{amount:,.2f} {currency}"
    except (ValueError, TypeError):
        return f"0 {currency}"

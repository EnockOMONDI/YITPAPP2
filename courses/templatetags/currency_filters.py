"""
Currency formatting template filters for YITP
Ensures consistent USD currency display across the platform
"""

from django import template
from django.conf import settings

register = template.Library()


@register.filter
def format_currency(value):
    """
    Format a price value as USD currency
    
    Usage: {{ course.price|format_currency }}
    Output: $35 USD
    """
    try:
        if value is None or value == 0:
            return "Free"
        
        # Format as USD with proper symbol
        return f"${float(value):.0f} USD"
    except (ValueError, TypeError):
        return "Price not available"


@register.filter
def format_currency_short(value):
    """
    Format a price value as short USD currency (no USD suffix)
    
    Usage: {{ course.price|format_currency_short }}
    Output: $35
    """
    try:
        if value is None or value == 0:
            return "Free"
        
        # Format as USD with just the symbol
        return f"${float(value):.0f}"
    except (ValueError, TypeError):
        return "N/A"


@register.filter
def format_installment(value):
    """
    Format installment amount (50% of price)
    
    Usage: {{ course.price|format_installment }}
    Output: $17.50 USD
    """
    try:
        if value is None or value == 0:
            return "Free"
        
        installment_amount = float(value) / 2
        return f"${installment_amount:.2f} USD"
    except (ValueError, TypeError):
        return "N/A"


@register.simple_tag
def currency_symbol():
    """
    Return the platform's currency symbol
    
    Usage: {% currency_symbol %}
    Output: $
    """
    return "$"


@register.simple_tag
def currency_code():
    """
    Return the platform's currency code
    
    Usage: {% currency_code %}
    Output: USD
    """
    return getattr(settings, 'PAYMENT_CURRENCY', 'USD')

from django import template
from cards.models import SiteSettings

register = template.Library()

@register.filter
def format_currency(value):
    """Format price based on site currency settings"""
    try:
        settings = SiteSettings.get_settings()
        currency = settings.currency
        
        # Convert to float
        amount = float(value)
        
        # Format based on currency
        if currency == 'VND':
            # VND doesn't use decimal places
            return f"{int(amount):,}₫"
        elif currency == 'USD':
            return f"${amount:,.2f}"
        elif currency == 'EUR':
            return f"€{amount:,.2f}"
        elif currency == 'GBP':
            return f"£{amount:,.2f}"
        elif currency == 'JPY':
            return f"¥{int(amount):,}"
        else:
            return f"{amount:,.2f}"
    except:
        return value

@register.simple_tag
def currency_symbol():
    """Get just the currency symbol"""
    try:
        settings = SiteSettings.get_settings()
        currency = settings.currency
        
        symbols = {
            'VND': '₫',
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'JPY': '¥'
        }
        return symbols.get(currency, '$')
    except:
        return '$'
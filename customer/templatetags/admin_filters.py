from django import template
from django.template.defaultfilters import floatformat
import calendar

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Obtiene un elemento de un diccionario por clave"""
    if dictionary and key in dictionary:
        return dictionary[key]
    return None

@register.filter
def month_name(month_number):
    """Convierte un número de mes a su nombre en español"""
    month_names = {
        1: 'Enero',
        2: 'Febrero',
        3: 'Marzo',
        4: 'Abril',
        5: 'Mayo',
        6: 'Junio',
        7: 'Julio',
        8: 'Agosto',
        9: 'Septiembre',
        10: 'Octubre',
        11: 'Noviembre',
        12: 'Diciembre'
    }
    return month_names.get(month_number, f'Mes {month_number}')

@register.filter
def format_currency(value):
    """Formatea un valor como moneda"""
    if value is None:
        return '$0.00'
    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return '$0.00'

@register.filter
def format_percentage(value):
    """Formatea un valor como porcentaje"""
    if value is None:
        return '0.0%'
    try:
        return f"{float(value):.1f}%"
    except (ValueError, TypeError):
        return '0.0%'

@register.filter
def profit_class(value):
    """Retorna la clase CSS para el color de utilidad"""
    if value is None:
        return 'profit-neutral'
    try:
        if float(value) > 0:
            return 'profit-positive'
        elif float(value) < 0:
            return 'profit-negative'
        else:
            return 'profit-neutral'
    except (ValueError, TypeError):
        return 'profit-neutral'


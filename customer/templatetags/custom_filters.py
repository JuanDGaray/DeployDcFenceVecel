from typing import Dict
import json
from django import template
from datetime import timedelta, date, datetime
register = template.Library()

@register.filter
def currency_usd(value):
    try:
        value = float(value)
        return "${:,.2f}".format(value)
    except (ValueError, TypeError):
        return "$0.00"

    
@register.filter
def add_days(value, days):
    if value:
        return value + timedelta(days=days)
    return value



@register.filter
def days_since(value):
    """
    Calcula cuántos días han pasado desde la fecha dada hasta hoy.
    Convierte una cadena de texto a un objeto de fecha si es necesario.
    """
    if not value:
        return "N/A"  # Devuelve N/A si el valor es nulo o no válido.

    # Convertir a fecha si es una cadena
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, "%Y-%m-%d").date()  # Ajusta el formato si es necesario
        except ValueError:
            return "Invalid date format"

    # Calcular la diferencia en días
    today = date.today()
    delta = today - value
    return delta.days

@register.filter
def type_of(value):
    if isinstance(value, str):
        return "string"
    elif isinstance(value, list):
        return "list"
    elif isinstance(value, dict):
        return "dict"
    else:
        return "unknown"
        
@register.filter(name='get_item')
def get_item(dictionary, key):
    if isinstance(dictionary, str):
        try:
            dictionary = json.loads(dictionary)
        except json.JSONDecodeError:
            dictionary = {}
    
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None 


@register.filter(name='get_item_value')
def get_item_value(dictionary, key):
    if isinstance(dictionary, str):
        try:
            dictionary = json.loads(dictionary)
        except json.JSONDecodeError:
            dictionary = {} 
    if isinstance(dictionary, dict):
        item_value = dictionary.get(key)
        if isinstance(item_value, dict):
            return item_value.get('total')
    return None

@register.filter(name='get_Subitem')
def get_Subitem(dictionary, key):
    if isinstance(dictionary, str):
        try:
            dictionary = json.loads(dictionary)
        except json.JSONDecodeError:
            dictionary = {}
    
    if isinstance(dictionary, dict):
        item_value = dictionary.get(key)
        if isinstance(item_value, dict):
            sub_items = item_value.get('subItems')
            if isinstance(sub_items, dict):
                result = []
                for k, v in sub_items.items():
                    if isinstance(v, dict):
                        total_sum = sum(value for value in v.values() if isinstance(value, (int, float)))
                        result.append((k, sorted(v.items()), total_sum))
                    else:
                        result.append((k, v, 0 ))
                print(result)
                return result
    return []


@register.filter(name='get_description')
def get_description(dictionary):
    print(dictionary)

    if isinstance(dictionary, dict):
        item_value = dictionary
        print(dictionary)


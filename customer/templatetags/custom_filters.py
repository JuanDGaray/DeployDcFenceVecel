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
def split_lines(value):
    """Split text by newlines into a list of paragraphs (non-empty lines). For use in templates to render scope paragraph by paragraph."""
    if value is None:
        return []
    if isinstance(value, str):
        return [s.strip() for s in value.splitlines() if s.strip()]
    if isinstance(value, list):
        return value
    return [str(value)]


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
            total = item_value.get('total', 0)
            if isinstance(sub_items, dict):
                result = []
                for k, v in sub_items.items():
                    if isinstance(v, dict):
                        result.append((k, sorted(v.items()), total))
                    else:
                        result.append((k, v, total))
                return result
    return []


@register.filter(name='get_description')
def get_description(dictionary):
    print(dictionary)

    if isinstance(dictionary, dict):
        item_value = dictionary
        print(dictionary)

@register.filter(name='short_name')
def short_name(first_name, last_name):
    return f"{first_name.split(' ')[0]} {last_name.split(' ')[0]}"

@register.filter(name='sum_values')
def sum_values(value):
    """
    Suma todos los valores numéricos de una lista, diccionario o valor individual.
    Especialmente diseñado para sumar costValues de items de costo real.
    """
    if value is None:
        return 0
    
    # Si es una lista de tuplas (como subItem.1), sumar los costValues
    if isinstance(value, list):
        total = 0
        for item in value:
            if isinstance(item, tuple) and len(item) >= 2:
                # Si es una tupla, buscar el costValue en el segundo elemento
                second_item = item[1]
                if isinstance(second_item, dict) and 'costValue' in second_item:
                    cost_value = second_item['costValue']
                    if isinstance(cost_value, (int, float)):
                        total += cost_value
                    elif isinstance(cost_value, str):
                        try:
                            total += float(cost_value)
                        except (ValueError, TypeError):
                            pass
            elif isinstance(item, (int, float)):
                total += item
            elif isinstance(item, dict):
                # Si es un diccionario, buscar costValue o sumar todos los valores numéricos
                if 'costValue' in item:
                    cost_value = item['costValue']
                    if isinstance(cost_value, (int, float)):
                        total += cost_value
                    elif isinstance(cost_value, str):
                        try:
                            total += float(cost_value)
                        except (ValueError, TypeError):
                            pass
                else:
                    # Sumar todos los valores numéricos del diccionario
                    for v in item.values():
                        if isinstance(v, (int, float)):
                            total += v
        return total
    
    # Si es un diccionario, buscar costValue o sumar todos los valores numéricos
    elif isinstance(value, dict):
        total = 0
        if 'costValue' in value:
            cost_value = value['costValue']
            if isinstance(cost_value, (int, float)):
                total += cost_value
            elif isinstance(cost_value, str):
                try:
                    total += float(cost_value)
                except (ValueError, TypeError):
                    pass
        else:
            # Sumar todos los valores numéricos del diccionario
            for v in value.values():
                if isinstance(v, (int, float)):
                    total += v
        return total
    
    # Si es un número, devolverlo directamente
    elif isinstance(value, (int, float)):
        return value
    
    # Si es una cadena, intentar convertirla a número
    elif isinstance(value, str):
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0
    
    return 0

@register.filter(name='multiply')
def multiply(value, arg):
    """
    Multiplica un valor por otro.
    """
    try:
        value = float(value)
        arg = float(arg)
        return value * arg
    except (ValueError, TypeError):
        return 0

@register.filter(name='get_nested_item')
def get_nested_item(dictionary, key_path):
    """
    Obtiene un valor anidado de un diccionario usando una ruta de claves separada por puntos.
    Ejemplo: get_nested_item:category_name.percentage
    """
    if not dictionary or not key_path:
        return None
    
    keys = key_path.split('.')
    current = dictionary
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    
    return current

@register.filter(name='add')
def add(value, arg):
    """
    Suma dos valores numéricos.
    """
    try:
        value = float(value)
        arg = float(arg)
        return value + arg
    except (ValueError, TypeError):
        return 0

@register.filter(name='concat_co')
def concat_co(value):
    """
    Concatena 'CO' con el número del change order.
    Ejemplo: concat_co:1 -> 'CO1'
    """
    try:
        return f"CO{value}"
    except (ValueError, TypeError):
        return f"CO{value}"
from typing import Dict
import json
from django import template
from datetime import timedelta
register = template.Library()

@register.filter
def currency_usd(value):
    try:
        # Formatea el número como USD con separadores de miles y dos decimales
        return "${:,.2f}".format(value)
    except (ValueError, TypeError):
        return "$0.00"
    
@register.filter
def add_days(value, days):
    if value:
        return value + timedelta(days=days)
    return value
    
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


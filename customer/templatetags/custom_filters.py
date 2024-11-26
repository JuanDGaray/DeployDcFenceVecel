from django import template

register = template.Library()

@register.filter
def currency_usd(value):
    try:
        # Formatea el número como USD con separadores de miles y dos decimales
        return "${:,.2f}".format(value)
    except (ValueError, TypeError):
        return "$0.00"
    
@register.filter    
def get_item(dictionary, key):
    print(dictionary)
    return dictionary.get(key)
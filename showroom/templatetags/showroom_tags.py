import urllib.parse

from django import template

register = template.Library()


@register.filter
def lookup(mapping, key):
    """Look up a key in a dictionary. ``{{ t|lookup:key }}``."""
    if not mapping:
        return ''
    return mapping.get(key, '')


@register.filter
def whatsapp_url(item, site):
    """Build a wa.me link for a product with the model name prefilled."""
    number = ''.join(ch for ch in (site.whatsapp or site.phone_primary or '') if ch.isdigit())
    number = number[-10:] if number else ''
    if not number:
        return ''
    if hasattr(item, 'name'):
        text = f'Hello, I want to know about {item.name}.'
    else:
        text = str(item)
    return f'https://wa.me/{number}?text={urllib.parse.quote(text)}'


@register.filter
def wa_text(text):
    return urllib.parse.quote(str(text))

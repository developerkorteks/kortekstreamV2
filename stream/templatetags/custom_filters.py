from django import template
import json
import pprint

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Get an item from a dictionary using a key.
    Usage: {{ dictionary|get_item:key }}
    """
    if dictionary is None:
        return None
    
    return dictionary.get(key, None)

@register.filter
def pprint(obj):
    """
    Pretty print an object.
    Usage: {{ object|pprint }}
    """
    if obj is None:
        return "None"
    
    try:
        # Try to convert to JSON for better formatting
        return json.dumps(obj, indent=2, sort_keys=True, default=str)
    except:
        # Fallback to pprint if JSON conversion fails
        return pprint.pformat(obj, indent=2, width=120)
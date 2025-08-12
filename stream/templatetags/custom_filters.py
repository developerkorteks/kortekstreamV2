from django import template
import json
import pprint
import base64

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

@register.filter
def make_dict(value, key):
    """
    Create a dictionary with the given key and value.
    Usage: {{ value|make_dict:"key" }}
    """
    return {key: value}

@register.filter
def encode_episode_id(episode_data, category='anime'):
    """
    Encode episode data into a base64 string for cleaner URLs.
    Usage: {{ episode_data|encode_episode_id:category }}
    """
    if not episode_data:
        return ''
        
    # Remove empty values
    data = {k: v for k, v in episode_data.items() if v}
    
    # Add category
    data['category'] = category
    
    # Convert to JSON and encode to base64
    json_str = json.dumps(data)
    encoded = base64.urlsafe_b64encode(json_str.encode()).decode()
    return encoded

@register.filter
def split(value, delimiter):
    """
    Split a string by delimiter.
    Usage: {{ string|split:"delimiter" }}
    """
    if not value or not isinstance(value, str):
        return []
    
    return value.split(delimiter)

@register.filter
def slice(value, arg):
    """
    Return a slice of the list.
    Usage: {{ list|slice:"start:end" }} or {{ list|slice:"start" }}
    """
    if not value:
        return []
    
    try:
        if ':' in arg:
            start, end = map(lambda x: int(x) if x else None, arg.split(':'))
            return value[start:end]
        else:
            return value[int(arg)]
    except (ValueError, IndexError):
        return []
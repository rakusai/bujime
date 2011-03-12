import types
import urllib
from django import template
	 
register = template.Library()
 
@register.filter
def urlencode(value):
    if type(value) is types.UnicodeType:
        return urllib.quote(value.encode("utf-8","ignore"))
    elif type(value) is types.StringType:
        return urllib.quote(value)
        
    return value
        
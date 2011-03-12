from django import template
import re
import xml.sax.saxutils
	 
register = template.Library()
 
@register.filter
def escape_link(value):
    return re.sub(r'(https?:\/\/[a-zA-Z0-9_\.\/\~\%\:\#\?=&\;\-]+)',	ur'<a href="\1" target="_blank">\1</a>' , xml.sax.saxutils.escape(value))

@register.filter
def escape_link_br(value):
    value = xml.sax.saxutils.escape(value)
    value = value.replace(" ","&nbsp;")
    value = value.replace("\t","").replace("\n","<br />")
    return re.sub(r'(https?:\/\/[a-zA-Z0-9_\.\/\~\%\:\#\?=&\;\-]+)',	ur'<a href="\1" target="_blank">\1</a>' , value)

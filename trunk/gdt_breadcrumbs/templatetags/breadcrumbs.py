from django import template

register = template.Library()

@register.inclusion_tag('breadcrumb_tag.djt', takes_context=True)
def breadcrumb_trail(context):
  from gdt_breadcrumbs import BREADCRUMB_URL, BREADCRUMB_TRAIL
  from django.conf import settings
  trail = []
  if 'request' in context:
    urls = context['request'].session.get(BREADCRUMB_URL, [])
    crumbs = context['request'].session.get(BREADCRUMB_TRAIL, {})
    for url in urls:
      trail.append((url, crumbs.get(url, url)))
  if not trail:
    trail = ((settings.GDT_BREADCRUMB_ROOT_URL, settings.GDT_BREADCRUMB_ROOT_TITLE),)
  return { 'breadcrumbs' : trail }

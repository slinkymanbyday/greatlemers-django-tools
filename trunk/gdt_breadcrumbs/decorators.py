def breadcrumb(title=None, reset=False, include=True):
  def breadcrumb_decorator(f):
    def breadcrumbed(request, *args, **kwargs):
      return f(request, *args, **kwargs)
    breadcrumbed.reset_breadcrumbs = reset
    breadcrumbed.include_breadcrumbs = include
    breadcrumbed.breadcrumb_title = title
    return breadcrumbed
  return breadcrumb_decorator

def breadcrumb_reset(title):
  return breadcrumb(title=title, reset=True, include=True)

def breadcrumb_include(title):
  return breadcrumb(title=title, reset=False, include=True)

def breadcrumb_ignore():
  return breadcrumb(title=None, reset=False, include=False)

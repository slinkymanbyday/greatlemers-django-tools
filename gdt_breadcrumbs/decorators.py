def breadcrumb(title=None, reset=False, include=True):
  """Decorator for saying how a view should manipulate the breadcrumb trail.

  All arguments can optionally have a callable passed to them.  In those
  situations, the callable will have the arguments from the view passed to it
  in order to determine what the actual value should be.

  Keyword arguments:
  title -- Either a callable or a string that will represent the text of the
           crumb to be added to the trail.
  reset -- Either a callable or a boolean representing whether the breadcrumb
           trail should be reset to the home crumb or not.
  include -- Either a callable or a boolean representing whether the view should
             cause a new crumb to be added to the trail.

  Returns:
  A decorated version of the view with the settings attached so that middleware
  can determine how to manipulate the breadcrumb trail for each view.
  """
  def breadcrumb_decorator(f):
    def breadcrumbed(request, *args, **kwargs):
      return f(request, *args, **kwargs)
    breadcrumbed.reset_breadcrumbs = reset
    breadcrumbed.include_breadcrumbs = include
    breadcrumbed.breadcrumb_title = title
    return breadcrumbed
  return breadcrumb_decorator

def breadcrumb_reset(title):
  """Shortcut decorator for views that should reset the trail and add a crumb.

  For more information see the help for breadcrumb.

  Keyword arguments:
  title -- Either a callable or a string that will represent the text of the
           crumb to be added to the trail.

  Returns:
  A decorated version of the view with the settings attached so that middleware
  can determine how to manipulate the breadcrumb trail for each view.
  """
  return breadcrumb(title=title, reset=True, include=True)

def breadcrumb_include(title):
  """Shortcut decorator for views that don't reset the trail but do add a crumb.

  For more information see the help for breadcrumb.

  Keyword arguments:
  title -- Either a callable or a string that will represent the text of the
           crumb to be added to the trail.

  Returns:
  A decorated version of the view with the settings attached so that middleware
  can determine how to manipulate the breadcrumb trail for each view.
  """
  return breadcrumb(title=title, reset=False, include=True)

def breadcrumb_ignore():
  """Shortcut decorator for views which shouldn't affect the trail.

  This is the same as the default option of not decorating the view.
  For more information see the help for breadcrumb.

  Returns:
  A decorated version of the view with the settings attached so that middleware
  can determine how to manipulate the breadcrumb trail for each view.
  """
  return breadcrumb(title=None, reset=False, include=False)

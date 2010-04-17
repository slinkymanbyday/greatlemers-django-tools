class BreadcrumbTracker(object):
  def process_view(self, request, view_function, view_args, view_kwargs):
    from gdt_breadcrumbs import BREADCRUMB_URL, BREADCRUMB_TRAIL
    from django.conf import settings
    reset = getattr(view_function, 'reset_breadcrumbs', False)
    if reset is True or (callable(reset) \
        and reset(request, view_args, view_kwargs)) or \
        BREADCRUMB_URL not in request.session:
      request.session[BREADCRUMB_TRAIL] = {settings.GDT_BREADCRUMB_ROOT_URL: settings.GDT_BREADCRUMB_ROOT_TITLE,}
      request.session[BREADCRUMB_URL] = [settings.GDT_BREADCRUMB_ROOT_URL]
      request.session.modified = True
    include = getattr(view_function, 'include_breadcrumbs', False)
    if include is True or (callable(include) \
        and include(request, view_args, view_kwargs)):
      if request.path in request.session[BREADCRUMB_URL]:
        url_index = request.session[BREADCRUMB_URL].index(request.path)
        for url in request.session[BREADCRUMB_URL][url_index:]:
          if url in request.session[BREADCRUMB_TRAIL]:
            del request.session[BREADCRUMB_TRAIL][url]
        request.session[BREADCRUMB_URL] = request.session[BREADCRUMB_URL][:url_index]
      request.session[BREADCRUMB_URL].append(request.path)
      if callable(view_function.breadcrumb_title):
        title = view_function.breadcrumb_title(request, view_args, view_kwargs)
      else:
        title = unicode(view_function.breadcrumb_title)
      request.session[BREADCRUMB_TRAIL][request.path] = title
      request.session.modified = True

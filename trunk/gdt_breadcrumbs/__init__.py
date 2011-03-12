"""
A django app for generating breadcrumb trails.

This app provides functionality to track a user's route through a site and to
generate a breadcrumb trail for them to see how they got to their current
location and to provide a quick route back to any of their previous pages.

The trail works by tracking decorated views and storing the route in the
session.  When a user visits a 'reset' page (see below) the trail will be pushed
back to the 'home' crumb and start again from there.  When a user visits a view
that's already in the trail then the trail will automatically jump back to that
point (even if they got view to that page without using the breadcrumb
navigation).

Usage is simple; First add the following two options to your settings file:
* GDT_BREADCRUMB_ROOT_URL - This should be the url the 'home' link on the trail
                            should point to.
* GDT_BREADCRUMB_ROOT_TITLE - This should be the title to be given to the 'home'
                              link on the trail.
Whilst in the settings file also add the gdt_breadcrumbs app and the
BreadcrumbTracker middleware to the appropriate places (it shouldn't matter
where the middleware is located as long as it's after the session middleware).

Secondly decorate any views that you wish to take part in the trail with one of
the provided decorators:
* breadcrumb_reset - This takes a title as a parameter and whenever the view is
                     visited it will reset the breadcrumb trail back to the
                     'home' link and then add a crumb for the current view after
                     it.
* breadcrumb_include - This also takes a title as a parameter but instead of
                       reseting the trail back to the 'home' link it will just
                       append the crumb to the end of the current trail.
* breadcrumb_ignore - This is the same as not decorating a view and will not
                      cause any changes to the breadcrumb trail.  This does not
                      take any parameters.
* breadcrumb - This is the master function that the other three provide
               shortcuts too.  It takes three parameters, title, reset and
               include - title represents the title to add to the breadcrumb
               trail, reset represents whether the trail should reset to the
               'home' link before adding any new crumbs and include represents
               whether a crumb should be added.
Whilst generally you will just need a static option for your view, it is also
possible to pass in callables to the title, reset and include options.  When
this happens the function will be called with the same parameters as the view
would have been and the result will be used as the value for that option.

Thirdly add the breadcrumb_trail template tag to your template and with a little
bit of styling you're ready to go!
"""

__version__ = "1.0 beta"
BREADCRUMB_URL = '_gdt_breadcrumbs_urls'
BREADCRUMB_TRAIL = '_gdt_breadcrumbs_crumbs'

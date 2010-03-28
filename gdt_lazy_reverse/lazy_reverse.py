class lazy_reverse(str):
    """A very simple class that represents a delayed url reverse.

    There are times when you may want the convenience of using a named url but
    are unable to due to the name not existing yet.  This is almost exclusively
    in a project/app's urls.py when you want to set something like a redirect
    url for a view whilst populating urlpatterns.  It should be called in the
    same way as a normal call to reverse should be made.
    """

    def __init___(self, viewname, urlconf=None, args=None, \
                  kwargs=None, prefix=None, current_app=None):
        """Constructor mimics the signature of django's reverse.

        All the parameters are the same as those taken by the reverse function
        found in django.core.urlresolvers
        """

        # Initialise the str base class as if we had an empty string.
        super(str,self).__init__("")

        # Store the other parameters for later.
        self._viewname = viewname
        self._urlconf = urlconf
        self._args = args
        self._kwargs = kwargs
        self._prefix = prefix
        self._current_app = current_app

        # This will be used later to cache the result of the lookup when it's
        # finally performed.
        self._url = None

    def __str__(self):
        """Returns the result of the requested lookup.

        If the lookup has not been done previously, perform it and cache the
        result before returning it.  Otherwise return the cached version.
        """

        if self._url is None:
            from django.core.urlresolvers import reverse
            self._url = reverse(viewname=self._viewname,
                                urlconf=self._urlconf,
                                args=self._args,
                                kwargs=self._kwargs,
                                prefix=self._prefix,
                                current_app=self._current_app
        return self._url

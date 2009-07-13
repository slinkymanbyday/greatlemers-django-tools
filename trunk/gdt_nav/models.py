from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.exceptions import FieldError
from django.core.urlresolvers import reverse, get_resolver, NoReverseMatch
from django.db import models
from django.utils.translation import ugettext as _


class MenuGroup(models.Model):
  """A grouping of menu options.

  A MenuGroup represents a collection of menu objects.  For example there may
  be a group of menu items for a horizontal navigation bar, and a different
  group for a vertical menu bar.

  """
  name = models.CharField(max_length=256,
                          help_text="A name that can be used to identify a group of menu items e.g. 'side menu' or 'top menu'.")
  notes = models.TextField(blank=True, default='',
                           help_text="Any extra info about this menu group (will not be publically visible).")

  def __unicode__(self):
    return self.name

  def __str__(self):
    return self.name

  def __repr__(self):
    return """<MenuGroup "%s">""" % self.name

  def generate_hierarchy(self, request):
    """Generate the menu hierarchy for this MenuGroup.

    Generate a set of lists that represent the hierarchy of menu options that
    are associated with this menu group.

    Keyword arguments:
    request -- The request object for the view that wants to generate some
               menus.

    Returns:
    A tuple of (displayable_options, selected_options, selected_params)
    displayable_options -- A dictionary mapping a parent menu item (either a
                           MenuOption object or the string 'ROOT' for the top
                           level of the menu) to a list of MenuOption objects
                           which sit on a sub menu below the key option.
    selected_options -- A dictionary mapping MenuOptions to a boolean.  Each
                        key is a menu option that either represents the current
                        url or is an ancestor of that option.  The boolean
                        values represent whether the option actually is
                        representing the current url.
    selected_params -- A dictionary that represent the keyword parameters that
                       can be used to generate the url if using the reverse
                       function or the url template tag.

    """

    # The user is required for checking access permissions.
    user = request.user

    # Start by obtaining a sorted list of the options to be used.
    menu_options = self.menu_items.order_by('ordering')
    if Site._meta.installed:
      # If the Sites app has been installed then filter by site id.
      menu_options = menu_options.filter(sites__id__exact=settings.SITE_ID)

    if user.is_anonymous():
      # Filter out anything that can't be seen by an anonymous user.
      menu_options = menu_options.filter(show_to_anonymous=True)
    else:
      # Build up a filter, we know we definitely want everything that logged
      # in users can see.
      query_filter = models.Q(show_to_authenticated=True)
      if user.is_staff:
        # Staff get to see anything authenticated users can see as well as what
        # only they are allowed to see.
        query_filter |= models.Q(show_to_staff=True)
      menu_options = menu_options.filter(query_filter)

    # Initialise variables to store options.
    matched_options = [] # options that are visible and match the current url
    visible_options = [] # options that are visible

    # Loop through the remaining options to see if firstly the user has
    # permission to see the option and secondly if the option should be
    # selected.
    url, url_name, url_kwargs = self._fetch_current_url_parts(request)
    for menu_option in menu_options:
      # If the user is anonymous then they will be able to see all remaining
      # menu options.  If they are not anonymous then we need to ensure they
      # have the valid permissions to see the option.
      # Also check to ensure the MenuOption can be generated correctly (make
      # sure that it has all the required named_url arguments etc.)
      if (user.is_anonymous()\
        or user.has_perms(menu_option.permissions.all()))\
        and menu_option.can_generate(url_kwargs):
        # Mark the option as visible to the user
        visible_options.append(menu_option)
        # Check to see if the menu option is a match for the current url
        if menu_option.url_matches(url, url_name, url_kwargs):
          # Mark the option as a match
          matched_options.append((menu_option, url_kwargs))

    # Loop through matched options to locate which option should be selected
    # the first option whose ancestors are all visible will be used.
    for option, params in matched_options:
      opt = option
      # Assume that this option is the one and intialise variables as such.
      selected_options = {option:True,} # options in the selected hierarchy.
      selected_params  = params # url keyword arguments for this option.
      # Check if the option is on the root level.
      if opt.parent is None:
        # Break out of the for loop as we've found our option.
        break
      # Loop until we get to a root level item.
      while opt.parent is not None:
        # Check if the parent option can be seen for this request.
        if opt.parent not in visible_options:
          # Break out of the while loop to try the next option.
          break
        else:
          # Add the parent to the list of selected options as a non matching
          # option.
          selected_options[opt.parent] = False
        # Move up the hierarchy to check the parent.
        opt = opt.parent
      else:
        # As we didn't break out of the while loop that means all options up to
        # the root level were visible and so we're done - therefore break out
        # of the for loop.
        break
    else:
      # No matching option was found since we didn't break out of the loop
      # therefore reset the return variables to empty dictionaries.
      selected_options = {}
      selected_params  = {}
    # Initialise the dictionary of displayable options with the keys being
    # 'ROOT' and the options in selected_options.
    displayable_options = {'ROOT':[]}
    for option in selected_options:
      displayable_options[option] = []

    # Loop through the visible options to eliminate any whose parent isn't
    # one of the lucky ones to be expanded (or None).
    for option in visible_options:
      # Check if the option has a parent.
      if option.parent is None:
        # No parent means the option should exist on the ROOT level.
        displayable_options['ROOT'].append(option)
      elif option.parent in selected_options.keys():
        # If the parent is a selcted option the add the option to its
        # sub-menu.
        displayable_options[option.parent].append(option)
    return displayable_options, selected_options, selected_params

  def _fetch_current_url_parts(self, request):
    """Helper function that reports information on the request's url.

    This utility function takes a request and analyses its url to generate the
    url_name and keyword arguments that can be used to generate the url via
    the reverse function or url tag.
    The url resolver doesn't return the name of the url that produces the
    given url so some hunting around has to be done to determine what exactly
    it should be.

    Keyword arguments:
    request -- The request object for the view that wants to generate some
               menus.

    Returns:
    A tuple of (url, url_name, url_kwargs)
    url -- The absolute representation of the requested url
    url_name -- The 'reversable' name of the requested url
    url_kwargs -- The keyword arguments that would be needed in order to
                  'reverse' the url.

    """

    # Start by fetching the path from the request and using it to build
    # the full url.
    path = request.path
    url = request.build_absolute_uri(path)

    # The url resolver which will generate some of the url info.
    resolver = get_resolver(None)

    # Pull out the view function, and the url arguments and keywords.
    view_func, url_args, url_kwargs = resolver.resolve(path)

    # Fetch a list of all the signatures of the items that can be reversed
    # to produce the view function.
    sigs = resolver.reverse_dict.getlist(view_func)

    url_name = None
    # Loop through all the items in the reverse dictionary.
    for key, value in resolver.reverse_dict.items():
      # Check if the value of the mapping is one of our matching signatures and
      # that the key is a string.
      if value in sigs and type(key) == str:
        try:
          # See if we have the right parameters to use this reversal and that
          # it produces the correct url.
          if resolver.reverse(key, *url_args, **url_kwargs) == path[1:]:
            # No exceptions were thrown so we have the right parameters and
            # the path matched therefore we've found the url name we were
            # seeking - which of course means we can stop looking.
            url_name = key
            break
        except NoReverseMatch, e:
          # The parameters were wrong - ah well, maybe the next one will
          # succeed.
          pass
    return url, url_name, url_kwargs


class AbsoluteMenuOptionManager(models.Manager):
  """Manager that only creates/returns absolute url menu options.

  """
  def get_query_set(self):
    query_set = super(AbsoluteMenuOptionManager, self).get_query_set()
    return query_set.filter(option_type=MenuOption.ABSOLUTE_URL_MENU_OPTION)

  def create(self, **kwargs):
    kwargs['option_type'] = MenuOption.ABSOLUTE_URL_MENU_OPTION
    return super(AbsoluteMenuOptionManager, self).create(**kwargs)

class NamedMenuOptionManager(models.Manager):
  """Manager that only creates/returns named url menu options.

  """
  def get_query_set(self):
    query_set = super(NamedMenuOptionManager, self).get_query_set()
    return query_set.filter(option_type=MenuOption.NAMED_URL_MENU_OPTION)

  def create(self, **kwargs):
    kwargs['option_type'] = MenuOption.NAMED_URL_MENU_OPTION
    return super(NamedMenuOptionManager, self).create(**kwargs)

class ModelMenuOptionManager(models.Manager):
  """Manager that only creates/returns model menu options.

  """
  def get_query_set(self):
    query_set = super(ModelMenuOptionManager, self).get_query_set()
    return query_set.filter(option_type=MenuOption.MODEL_MENU_OPTION)

  def create(self, **kwargs):
    kwargs['option_type'] = MenuOption.MODEL_MENU_OPTION
    return super(ModelMenuOptionManager, self).create(**kwargs)


class MenuOption(models.Model):
  """A class to represent all menu options.

  """
  objects = models.Manager()
  absolute_menu_options = AbsoluteMenuOptionManager()
  named_menu_options = NamedMenuOptionManager()
  model_menu_options = ModelMenuOptionManager()

  # Template to use when producing menu options as links.
  link_template = """<a href="%(url)s" title="%(title)s"%%(classes)s>%(link_text)s</a>"""

  # Template to use when producing menu options as non-links.
  non_link_template = """<span title="%(title)s"%%(classes)s>%(link_text)s</span>"""

  # The different types of menu options that will be available.
  ABSOLUTE_URL_MENU_OPTION = 0
  NAMED_URL_MENU_OPTION = 1
  MODEL_MENU_OPTION = 2
  MODEL_TYPE_CHOICES = (
      (ABSOLUTE_URL_MENU_OPTION, 'Absolute URL Menu Option'),
      (NAMED_URL_MENU_OPTION, 'Named URL Menu Option'),
      (MODEL_MENU_OPTION, 'Model Menu Option'),
  )

  # Core fields, required by all menu options.
  name = models.CharField(max_length=256,
                          help_text="Text that should appear when the menu option is displayed (unless the option is a model menu option).")
  option_type = models.PositiveSmallIntegerField(choices=MODEL_TYPE_CHOICES,
                                                 default=ABSOLUTE_URL_MENU_OPTION,
                                                 help_text="The type of menu option.")
  alt_text = models.CharField(max_length=256,
                              help_text="Text that should appear when hovering over the link.")
  menu_group = models.ForeignKey('MenuGroup', related_name='menu_items',
                                 help_text="The menu group that the link belongs in.")
  ordering = models.IntegerField(help_text="The position of the item in the menu group or sub-menu.")
  permissions = models.ManyToManyField(Permission, null=True, blank=True,
                                       help_text="The permissions that the user must have to see this menu item (when logged in - ignored when the user is anonymous).")
  parent = models.ForeignKey('MenuOption', blank=True, null=True,
                             help_text="The menu item that comes above this one in the hierarchy (leave empty for top level items).")
  show_to_anonymous = models.BooleanField(default=False,
                                          help_text="Should this option be seen by anonymous users?")
  show_to_authenticated = models.BooleanField(default=True,
                                              help_text="Should the option be seen by authenticated users?")
  show_to_staff = models.BooleanField(default=True,
                                      help_text="Should this option be seen by admin users (takes precedence over show_to_authenticated)?")
  notes = models.TextField(blank=True, default='',
                           help_text="Any extra info about this option (will not be visible to users).")
  if Site._meta.installed:
    # If the Sites app has been installed then take advantage of it, otherwise
    # act as if it's not there.
    sites = models.ManyToManyField(Site, blank=True,
                                   help_text="The sites that should display this menu option.")

  # The following options are potentially required, depending on the type of menu option this represents.
  url = models.URLField(verify_exists=False, blank=True, null=True,
                        help_text="The absolute url that represents this option (required for absolute url menu options).")
  url_name = models.CharField(max_length=64, blank=True, null=True,
                              help_text="The 'reversable' url name that represents this option (required for named url and model menu options).")
  content_type = models.ForeignKey(ContentType, blank=True, null=True,
                                   help_text="The type of object to fetch and produce options for (required for model menu options).")
  manager = models.CharField(max_length=32, default='objects', blank=True, null=True,
                             help_text="The object manager to use when querying the content_type (required for model menu options).")
  query = models.TextField(blank=True, default='',
                           help_text="The query to use to filter down the content_type objects- format is as if entering directly into a django filter, comma separate multiple restrictions (required for model menu options if filtering is desired).")
  url_id = models.CharField(max_length=64, blank=True, null=True,
                            help_text="The id in the named url that this query provides (required for model menu options).")
  model_id = models.CharField(max_length=64, blank=True, null=True,
                              help_text="The local attribute to map to the url_id above (required for model menu options).")
  order_by = models.CharField(blank=True, default='', max_length=64,
                              help_text="Any sorting to be done on the query - format is as if entering directly into a django order_by filter, comma separate multiple order keys - will happen after filtering (required for model menu options).")
  result_limit = models.PositiveSmallIntegerField(blank=True, null=True,
                                                  help_text="Number of results to return (required for model menu options).")

  def __unicode__(self):
    return self.name

  def __str__(self):
    return self.name

  def __repr__(self):
    opt_type = ""
    if self.option_type == MenuOption.ABSOLUTE_URL_MENU_OPTION:
      opt_type = "Absolute"
    elif self.option_type == MenuOption.NAMED_URL_MENU_OPTION:
      opt_type = "Named"
    elif self.option_type == MenuOption.MODEL_MENU_OPTION:
      opt_type = "Model"
    return """<%sMenuOption "%s">""" % (opt_type, self.name)


  def as_link(self, url_params=None):
    """Generate an HTML tag representing this menu option as a link.

    Keyword arguments:
    url_params -- The url keyword arguments that can be used in the reverse
                  function or url template tag to generate a url
                  (default=None).

    """

    # If no params were passed in, turn the variable into an empty dictionary.
    url_params = url_params or {}
    # Check if we're dealing with a model.
    if self.option_type == MenuOption.MODEL_MENU_OPTION:
      # There's a special handler function to deal with this so use it.
      return self._generate_model_type_string(url_params, False)
    elif self.option_type == MenuOption.ABSOLUTE_URL_MENU_OPTION:
      # Otherwise when dealing with an absolute url plug it straight into the
      # template.
      string_params = { 'url': self.url,
                        'title': _(self.alt_text),
                        'link_text': _(self.name),
                      }
      return ((MenuOption.link_template % string_params, False),)
    elif self.option_type == MenuOption.NAMED_URL_MENU_OPTION:
      # When dealing with a named url generate it first then plug it into
      # the template.
      string_params = { 'url': self._generate_named_link(url_params),
                        'title': _(self.alt_text),
                        'link_text': _(self.name),
                      }
      return ((MenuOption.link_template % string_params, False),)



  def as_non_link(self, url_params=None):
    """Generate an HTML tag representing this menu option as a link.

    Keyword arguments:
    url_params -- The url keyword arguments that can be used in the reverse
                  function or url template tag to generate the current url
                  (default=None).

    """

    # If no params were passed in, turn the variable into an empty dictionary.
    url_params = url_params or {}
    # Check if we're dealing with a model.
    if self.option_type == MenuOption.MODEL_MENU_OPTION:
      # There's a special handler function to deal with this so use it.
      return self._generate_model_type_string(url_params, True)
    elif self.option_type == MenuOption.ABSOLUTE_URL_MENU_OPTION \
      or self.option_type == MenuOption.NAMED_URL_MENU_OPTION:
      # Otherwise when dealing with absolute or named urls just plug the
      # standard info into the template.
      string_params = { 'title': _(self.alt_text),
                        'link_text': _(self.name),
                      }
      return ((MenuOption.non_link_template % string_params, True),)

  def can_generate(self, kwargs):
    """Check to see if the option can be generated with the arguments provided.

    Keyword arguments:
    kwargs -- The url keyword arguments that can be used in the reverse
              function or url template tag to generate the current url.

    """

    # Check if we're dealing with a model.
    if self.option_type == MenuOption.MODEL_MENU_OPTION:
      # Will we get any results from the queryset?
      queryset = self._fetch_queryset(**kwargs)
      return queryset.count() > 0
    elif self.option_type == MenuOption.ABSOLUTE_URL_MENU_OPTION:
      # Absolute urls can always be generated.
      return True
    elif self.option_type == MenuOption.NAMED_URL_MENU_OPTION:
      # See if the named url can be generated.
      return self._generate_named_link(kwargs) is not None

  def show_hierarchy(self, selected):
    """Check if the menu option's children should be shown.

    Primarily used for model type options when the option representing the
    current url may be one of a number of items returned from a query result.

    Keyword arguments:
    selected -- Whether the item being displayed is in the list of selected
                options.

    """

    if self.option_type == MenuOption.MODEL_MENU_OPTION:
      # For models it depends on selected.
      return selected
    elif self.option_type == MenuOption.ABSOLUTE_URL_MENU_OPTION \
      or self.option_type == MenuOption.NAMED_URL_MENU_OPTION:
      # For absolute and named urls always display the children.
      return True

  def url_matches(self, url, url_name, url_kwargs):
    """Check if the current request's url matches this option.

    Keyword arguments:
    url -- The absolute url of the current request.
    url_name -- The 'reversable' name of the url for the current request.
    url_kwargs -- Keyword arguments required to 'reverse' the url_name and
                  produce the current request's url.

    """

    # Check if we're dealing with a model.
    if self.option_type == MenuOption.MODEL_MENU_OPTION:
      # If the url name doesn't match we're on to a non-starter so abort!
      if not self.url_name == url_name:
        return False
      # We need to filter our search results down to see if the query results
      # actually contain the url visited.
      filter_kwargs = { str(self.model_id):str(url_kwargs[self.url_id]),}
      queryset = self._fetch_queryset(filter_kwargs, **url_kwargs)
      return queryset.count() > 0
    elif self.option_type == MenuOption.ABSOLUTE_URL_MENU_OPTION:
      # Absolute items match if the url is a match
      return self.url == url
    elif self.option_type == MenuOption.NAMED_URL_MENU_OPTION:
      # Named items match if the url name matches
      return self.url_name == url_name

  def _fetch_queryset(self, *args, **kwargs):
    """Helper function to generate a queryset for model menu options.

    Keyword arguments:
    args -- Can take any number of dictionaries that will be applied as extra
            filters on the query.
    kwargs -- The url keyword arguments for the current request.
    """

    # Initialise to an empty set.
    queryset = MenuOption.objects.none()
    try:
      if self.query:
        # Expand the query with arguments from urls.
        full_query = str(self.query % kwargs)
        # Convert the string form of the query into a kwargs style dictionary
        query_kwargs = dict([a.strip().split('=') for a in full_query.split(',')])
      else:
        query_kwargs = {}
      # Get the object manager
      manager = getattr(self.content_type.model_class(), self.manager, None)
      # Generate the queryset
      queryset = manager.filter(**query_kwargs)
    except (KeyError, FieldError), e:
      # An expected potential error as the kwargs may not all exist or be in
      # the correct format.
      pass
    except Exception, x:
      # Unexpected exception, we should probably log something here.
      # TODO: Add some logging.
      pass
    # Any arguments passed in to args should be dictionaries that are to be used
    # as extra filters for the queryset.
    for extra_filter in args:
      queryset = queryset.filter(**extra_filter)
    # Apply any ordering instructions.
    if self.order_by:
      queryset = queryset.order_by(*self.order_by.split(','))
    # Limit the results.
    if self.result_limit:
      queryset = queryset[:self.result_limit]
    return queryset

  def _generate_model_type_string(self, url_params, can_select):
    """Helper function to generate a set of links for a model type option.

    Since a model type option may have more than one link in it this function
    will produce a list of the links for this option.  If one of the results
    matches then given url then it will actually be returned as a non-link
    instead.

    Keyword arguments:
    url_params -- The url keyword arguments for the current request.
    can_select -- Whether the current link should contain any non-links.

    Returns:
    A tuple of tuples, each inner tuple consisting of the link to be displayed
    followed by a boolean specifying if the url could be selected (and hence
    have its children displayed).

    """

    # Items to be plugged into the templates.
    string_params = { 'url': '',
                      'title': _(self.alt_text),
                      'link_text': _(self.name),
                    }
    results = []
    # Loop through all the items matched by this url.
    for obj in self._fetch_queryset(**url_params):
      string_params['url'] = self._generate_model_type_link(obj, url_params)

      # Rely on the fact that __unicode__ has been defined for the model being
      # used and that it will return an accurate description.
      string_params['link_text'] = unicode(obj)

      # Calculate whether the item in question matches the url arguments
      # This indicates that either this item or one of it's sub menus has
      # been selected.
      _model_value = str(getattr(obj, self.model_id, None))
      _url_args_value = str(url_params.get(self.url_id,False))
      is_selected = _model_value == _url_args_value

      # If the url match has been pinpointed to this group and the current
      # object matches the arguments then display as a span.
      # Otherwise show the link.
      if can_select and is_selected:
        results.append((MenuOption.non_link_template % string_params, True))
      else:
        results.append((MenuOption.link_template % string_params, is_selected))
    return results

  def _generate_model_type_link(self, obj, kwargs):
    """Helper function to generate a url for a result item of a model option.

    Keyword arguments:
    obj -- The result model object.
    kwargs -- The url keyword arguments from the current request's url.

    """

    try:
      url_kwargs = {}
      resolver = get_resolver(None)
      # Loop through the arguments required for reversing this url and extract
      # only the required ones from the request's keyword args.
      for arg_name in resolver.reverse_dict[self.url_name][0][0][1]:
        if arg_name == self.url_id:
          # If the argument is the extra one added by the model menu type then
          # put it in specially.
          url_kwargs[arg_name] = str(getattr(obj, self.model_id))
        elif arg_name not in kwargs:
          # If there's a missing argument then return None - there won't be
          # any link being generated here...
          return None
        else:
          # Otherwise just add it to the dictionary.
          url_kwargs[arg_name] = kwargs[arg_name]
      # Generate the url.
      url = reverse(self.url_name, kwargs=url_kwargs)
      return url
    except NoReverseMatch, e:
      return None

  def _generate_named_link(self, kwargs):
    """Helper function to generate a url for a named url menu option.

    Keyword arguments:
    kwargs -- The url keyword arguments from the current request's url.

    """

    try:
      url_kwargs = {}
      resolver = get_resolver(None)

      # Loop through the arguments required for reversing this url and extract
      # only the required ones from the request's keyword args.
      for arg_name in resolver.reverse_dict[self.url_name][0][0][1]:
        if arg_name not in kwargs:
          # If there's a missing argument then return None - there won't be
          # any link being generated here...
          return None
        else:
          # Otherwise just add it to the dictionary.
          url_kwargs[arg_name] = kwargs[arg_name]
      # Generate the url.
      url = reverse(self.url_name, kwargs=url_kwargs)
      return url
    except NoReverseMatch, e:
      return None

def _menu_option_pre_save_hook(sender, **kwargs):
  """Function to hook into the pre-save model signal and remove unwanted data.

  """

  menu_option = kwargs.get('instance')
  if menu_option is not None:
    if menu_option.option_type == MenuOption.ABSOLUTE_URL_MENU_OPTION:
      menu_option.url_name = None
      menu_option.content_type = None
      menu_option.manager = 'objects'
      menu_option.query = ''
      menu_option.url_id = ''
      menu_option.model_id = ''
      menu_option.order_by = ''
      menu_option.result_limit = None
    elif menu_option.option_type == MenuOption.NAMED_URL_MENU_OPTION:
      menu_option.url = None
      menu_option.content_type = None
      menu_option.manager = 'objects'
      menu_option.query = ''
      menu_option.url_id = ''
      menu_option.model_id = ''
      menu_option.order_by = ''
      menu_option.result_limit = None
    elif menu_option.option_type == MenuOption.MODEL_MENU_OPTION:
      menu_option.url = None
models.signals.pre_save.connect(_menu_option_pre_save_hook, sender=MenuOption)

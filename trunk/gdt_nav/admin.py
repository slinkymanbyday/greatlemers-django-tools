from models import MenuGroup, MenuOption
from django.core.urlresolvers import reverse, NoReverseMatch
from django.contrib.admin import site, ModelAdmin, VERTICAL
from django.contrib.sites.models import Site
from django.utils.functional import update_wrapper
from django.utils.translation import ugettext as _
from forms import AbsoluteMenuOptionForm, ModelMenuOptionForm,\
                  NamedMenuOptionForm
site.register(MenuGroup)

class MenuOptionAdmin(ModelAdmin):
  list_display = ('name', 'option_type', 'menu_group',)
  search_fields = ('name',)
  list_filter = ('show_to_anonymous',
                 'show_to_authenticated',
                 'show_to_staff',
                 'option_type',
                )
  ordering = ('menu_group', 'name',)
  filter_horizontal = ('permissions',)
  radio_fields = {'option_type':VERTICAL,}
  fieldsets = (
    (None, {'fields': ('option_type',
                       'name',
                       'alt_text',
                       'notes',
                      ),
           },
    ),
    ('Positioning',{'fields':((Site._meta.installed and ('sites',
                              'menu_group',
                              'parent',
                              'ordering',
                             )) or ('menu_group',
                              'parent',
                              'ordering',
                             )),
                    'description':'Settings describing where to display the menu item.',
                   },
    ),
    ('Permissions', {'classes': ('collapse',),
                     'fields': ('show_to_anonymous',
                                'show_to_authenticated',
                                'show_to_staff',
                                'permissions',
                               ),
                     'description':'Settings to determine who can see the menu item.',
                    },
    ),
    ('Extra Information', {'classes': ('collapse',),
                           'fields': ('url',
                                      'url_name',
                                      'content_type',
                                      'manager',
                                      'query',
                                      'url_id',
                                      'model_id',
                                      'order_by',
                                      'result_limit',
                                     ),
                           'description':'Extra information that may or may not be required depending on the type of menu option.',
                          },
    ),
  )

  def fetch_admin_class(self, option_type):
    if option_type == MenuOption.ABSOLUTE_URL_MENU_OPTION:
        admin_class = AbsoluteMenuOptionAdmin
    elif option_type == MenuOption.NAMED_URL_MENU_OPTION:
        admin_class = NamedMenuOptionAdmin
    elif option_type == MenuOption.MODEL_MENU_OPTION:
        admin_class = ModelMenuOptionAdmin
    else:
        admin_class = ModelAdmin
    return admin_class

  def __call__(self, request, url):
    if url is not None:
      import re
      matches = re.match('^add/(\d+)$',url)
      if matches:
        return self.add_view(request, option_type=matches.groups()[0])
    return ModelAdmin.__call__(self, request, url)

  def add_view(self, request, form_url='',
               extra_context=None, option_type=None):
    if extra_context is None:
      extra_context = {}
    extra_context['app_label'] = _("GDT Nav")
    extra_context['menu_option_types'] = MenuOption.MODEL_TYPE_CHOICES
    if option_type is not None:
      # Hack to detect if we need to specify the javascript url or not.
      try:
        reverse('admin:jsi18n')
      except NoReverseMatch, e:
        extra_context['jsurl'] = "../../../../jsi18n/"
      option_type = int(option_type)
      type = dict(MenuOption.MODEL_TYPE_CHOICES)[option_type]
      extra_context['crumb'] = _("Add %(name)s") % {'name':type}
      admin_class = self.fetch_admin_class(option_type)
      admin_instance = admin_class(MenuOption, self.admin_site)
      return admin_instance.add_view(request, form_url, extra_context)
    else:
      extra_context['default_form'] = True
      return ModelAdmin.add_view(self, request, form_url, extra_context)

  def change_view(self, request, object_id, extra_context=None):
    try:
      obj = self.queryset(request).get(pk=int(object_id))
      option_type = obj.option_type
    except (self.model.DoesNotExist, ValueError), e:
      option_type = None
    if extra_context is None:
      extra_context = {}
    extra_context['app_label'] = _("GDT Nav")
    extra_context['menu_option_types'] = MenuOption.MODEL_TYPE_CHOICES
    if option_type is not None:
      option_type = int(option_type)
      extra_context['crumb'] = obj.name
      admin_class = self.fetch_admin_class(option_type)
      admin_instance = admin_class(MenuOption, self.admin_site)
      return admin_instance.change_view(request, object_id, extra_context)
    else:
      extra_context['default_form'] = True
      return ModelAdmin.change_view(self, request, object_id, extra_context)

  def changelist_view(self, request, extra_context=None):
    if extra_context is None:
      extra_context = {}
    extra_context['menu_option_types'] = MenuOption.MODEL_TYPE_CHOICES
    extra_context['app_label'] = _("GDT Nav")
    return ModelAdmin.changelist_view(self, request, extra_context)

  def get_urls(self):
    from django.conf.urls.defaults import patterns, url
    urlpatterns = ModelAdmin.get_urls(self)
    def wrap(view):
      def wrapper(*args, **kwargs):
        return self.admin_site.admin_view(view)(*args, **kwargs)
      return update_wrapper(wrapper, view)
    info = (self.admin_site.name,
            self.model._meta.app_label,
            self.model._meta.module_name
           )
    urlpatterns = patterns('',
      url(r'^add/(?P<option_type>\d)/$',
          wrap(self.add_view),
          name='%sadmin_%s_%s_add_by_type' % info),
    ) + urlpatterns
    return urlpatterns

site.register(MenuOption, MenuOptionAdmin)
class AbsoluteMenuOptionAdmin(ModelAdmin):
  list_display = ('name', 'option_type', 'menu_group',)
  search_fields = ('name',)
  list_filter = ('show_to_anonymous',
                 'show_to_authenticated',
                 'show_to_staff',
                )
  ordering = ('menu_group', 'name',)
  filter_horizontal = ('permissions',)
  radio_fields = {'option_type':VERTICAL,}
  form = AbsoluteMenuOptionForm
  fieldsets = (
    (None, {'fields': ('name',
                       'alt_text',
                       'url',
                       'notes',
                       'option_type',
                      ),
           },
    ),
    ('Positioning',{'fields':((Site._meta.installed and ('sites',
                              'menu_group',
                              'parent',
                              'ordering',
                             )) or ('menu_group',
                              'parent',
                              'ordering',
                             )),
                    'description':'Settings describing where to display the menu item.',
                   },
    ),
    ('Permissions', {'classes': ('collapse',),
                     'fields': ('show_to_anonymous',
                                'show_to_authenticated',
                                'show_to_staff',
                                'permissions',
                               ),
                     'description':'Settings to determine who can see the menu item.',
                    },
    ),
  )

class NamedMenuOptionAdmin(ModelAdmin):
  list_display = ('name', 'option_type', 'menu_group',)
  search_fields = ('name',)
  list_filter = ('show_to_anonymous',
                 'show_to_authenticated',
                 'show_to_staff',
                )
  ordering = ('menu_group', 'name',)
  filter_horizontal = ('permissions',)
  radio_fields = {'option_type':VERTICAL,}
  form = NamedMenuOptionForm
  fieldsets = (
    (None, {'fields': ('name',
                       'alt_text',
                       'url_name',
                       'notes',
                       'option_type',
                      ),
           },
    ),
    ('Positioning',{'fields':((Site._meta.installed and ('sites',
                              'menu_group',
                              'parent',
                              'ordering',
                             )) or ('menu_group',
                              'parent',
                              'ordering',
                             )),
                    'description':'Settings describing where to display the menu item.',
                   },
    ),
    ('Permissions', {'classes': ('collapse',),
                     'fields': ('show_to_anonymous',
                                'show_to_authenticated',
                                'show_to_staff',
                                'permissions',
                               ),
                     'description':'Settings to determine who can see the menu item.',
                    },
    ),
  )

class ModelMenuOptionAdmin(ModelAdmin):
  list_display = ('name', 'option_type', 'menu_group',)
  search_fields = ('name',)
  list_filter = ('show_to_anonymous',
                 'show_to_authenticated',
                 'show_to_staff',
                )
  ordering = ('menu_group', 'name',)
  filter_horizontal = ('permissions',)
  radio_fields = {'option_type':VERTICAL,}
  form = ModelMenuOptionForm
  fieldsets = (
    (None, {'fields': ('name',
                       'alt_text',
                       'url_name',
                       'notes',
                       'option_type',
                      ),
           },
    ),
    ('Positioning',{'fields':((Site._meta.installed and ('sites',
                              'menu_group',
                              'parent',
                              'ordering',
                             )) or ('menu_group',
                              'parent',
                              'ordering',
                             )),
                    'description':'Settings describing where to display the menu item.',
                   },
    ),
    ('Permissions', {'classes': ('collapse',),
                     'fields': ('show_to_anonymous',
                                'show_to_authenticated',
                                'show_to_staff',
                                'permissions',
                               ),
                     'description':'Settings to determine who can see the menu item.',
                    },
    ),
    ('Model Information', {'fields': ('content_type',
                                      'manager',
                                      'query',
                                      'url_id',
                                      'model_id',
                                      'order_by',
                                      'result_limit',
                                     ),
                           'description':'Information describing the model and query that will select what should appear for this menu item.',
                          },
    ),
  )

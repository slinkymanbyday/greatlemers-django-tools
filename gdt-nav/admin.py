from models import MenuGroup, Article, MenuOption
from django.contrib.admin import site, ModelAdmin, VERTICAL
from django.contrib.sites.models import Site
site.register(MenuGroup)
site.register(Article)

class MenuOptionAdmin(ModelAdmin):
  list_display = ('name', 'option_type', 'menu_group',)
  search_fields = ('name',)
  list_filter = ('show_to_anonymous',
                 'show_to_authenticated',
                 'show_to_staff',
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

site.register(MenuOption, MenuOptionAdmin)
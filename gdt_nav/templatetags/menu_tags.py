from django import template
from django.template import RequestContext
from gdt_nav.models import MenuGroup, MenuOption


register = template.Library()

# Some templates to be used for describing how the menu depth class should be
# output, how items should be output and how groups of items should be output.
_menu_level_template = """menu_level_%s"""
_item_template = """<%(item_tag)s%(menu_option_id)s class="menu_item %(menu_level)s%(selected)s">%(item)s%(sub_list)s</%(item_tag)s>"""
_group_template = """<%(group_tag)s class="%(menu_level)s">%(group)s</%(group_tag)s>"""

@register.inclusion_tag("admin_menu_as_tag.html", takes_context=True)
def admin_menu_as_tag(context, menu_root, spaces='', last_item=True):
  """
  Return a menu group as an html structure based on the tag names passed in.

  Keyword arguments:
  context -- The current template context
  menu_root -- The collection of menu_options to convert, or the name of the
               desired collection.
  spaces -- A string representing the menu hierarchy drawing structure of the
            parent element.
  last_item -- Is this the last item of a group of menu options.


  """
  # If neither a menu group nor a menu option has been passed in then assume
  # it's a string naming the group to use and attempt to fetch it.
  item = None
  if type(menu_root) == MenuGroup:
    children = menu_root.menu_items.filter(parent__isnull=True).order_by('ordering')
  elif type(menu_root) == MenuOption:
    item = menu_root
    children = menu_root.menuoption_set.order_by('ordering')
  else:
    try:
      menu_root = MenuGroup.objects.get(name=menu_group)
      children = menu_root.menu_items.filter(parent__isnull=True).order_by('ordering')
    except:
      children = MenuGroup.objects.empty()
  space_string = spaces
  first_spaces = spaces + "&#9475;" + "<br />"
  second_spaces = "<br />" + spaces
  if last_item:
    space_string += "&#9584;"
    child_space_string = spaces + "&#12288;"
    second_spaces += "&#12288;"
  else:
    space_string += "&#9507;"
    child_space_string = spaces + "&#9475;"
    second_spaces += "&#9475;"
  if children.count() > 0:
    space_string += "&#9523;"
    second_spaces += "&#9475;"
  else:
    space_string += "&#9473;"
    second_spaces += "&#12288;"
  space_string += "&#9588;"
  return { "item":item,
           "children":children,
           "spaces":space_string,
           "child_spaces":child_space_string,
           "first_spaces":first_spaces,
           "second_spaces":second_spaces,
         }

@register.inclusion_tag("menu_as_tag.html", takes_context=True)
def menu_as_ul(context, menu_group):
  """
  Return a menu group as an html structure based around nested unordered lists.

  Keyword arguments:
  context -- The current template context
  menu_group -- The collection of menu_options to convert.

  """
  return menu_as_tag(context, menu_group, "ul", "li")

@register.inclusion_tag("menu_as_tag.html", takes_context=True)
def menu_as_div(context, menu_group):
  """
  Return a menu group as an html structure based around nested divs.

  Keyword arguments:
  context -- The current template context
  menu_group -- The collection of menu_options to convert.

  """
  return menu_as_tag(context, menu_group, "div", "div")

@register.inclusion_tag("menu_as_tag.html", takes_context=True)
def menu_as_tag(context, menu_group, group_tag="ul", item_tag="li"):
  """
  Return a menu group as an html structure based on the tag names passed in.

  Keyword arguments:
  context -- The current template context
  menu_group -- The collection of menu_options to convert, or the name of the
                desired collection.
  group_tag -- The tag to surround collections of menu items with (default ul).
  item_tag -- The tag to surround individual menu items with (default li).

  """
  # If a menu group's not been passed in then assume it's a string naming the
  # group to use and attempt to fetch it.
  if type(menu_group) != MenuGroup:
    try:
      menu_group = MenuGroup.objects.get(name=menu_group)
    except:
      return { "menu_string":"", }

  # Generate the menu hierarchy, a list of selected items and a list of the
  # named parameters that were used to form the url.
  hierarchies, selected_items, selected_params = menu_group.generate_hierarchy(context.get('request'))
  # Generate the html structure for the items just generated.
  menu_string = _generate_menu_string(hierarchies, "ROOT", selected_items,
                                      selected_params, group_tag, item_tag)
  return { "menu_string":menu_string, }

def _generate_menu_string(hierarchies, hier_index, selected_items,
                          selected_params, group_tag, item_tag, level=0):
  """
  Helper function to generate a string representation of a menu hierarchy.

  Keyword arguments:
  hierarchies -- A dictionary mapping menu options (or the string "ROOT") to a
                 list of options that should feature as a sub menu of that
                 option.
  hier_index -- The index into hierarchies dictionary to use.
  selected_items -- A list of menu options that either match the current url
                    or is an ancestor of an item that matches.
  selected_params -- The keyword arguments that were extracted from the
                     current url, and that could be used to recreate the url
                     via a reverse.
  group_tag -- The tag to surround collections of menu items with.
  item_tag -- The tag to surround individual menu items with.
  level -- The depth of the menu (default 0)

  """
  # Define the class name for the current menu depth.
  menu_level = _menu_level_template % level
  # There are no items to put in a sub menu here so return empty handed.
  if len(hierarchies[hier_index]) == 0:
    return ""
  # A list that will store strings representing a menu item (potentially with
  # a set of sub menu items too).
  sub_items = []
  # Loop through all menu item objects for this level of the hierarchy.
  for opt in hierarchies[hier_index]:
    # A container for the classes that will be added to the menu item begin
    # by giving it the menu depth.
    classes = [menu_level,]
    # If the option is marked as being the one where the url matched then
    # display it as a non-link otherwise we want to be able to click on it.
    # After assignment opts will be filled with a list of tuples, each
    # containing a string representing the item and a boolean indicating if the
    # item should receive the selected class name.
    if selected_items.get(opt,False):
      opts = opt.as_non_link(selected_params)
    else:
      opts = opt.as_link(selected_params)
    option_index = None
    if opt.option_type == MenuOption.MODEL_MENU_OPTION:
      option_index = 0
    # Loop through all the tuples we got back.
    for opt_string, opt_selected in opts:
      if not opt.menu_option_id:
        menu_option_id = ''
      elif option_index is not None:
        option_index += 1
        menu_option_id = " id='%s_%s'" % (opt.menu_option_id, option_index)
      else:
        menu_option_id = " id='%s'" % opt.menu_option_id
      # Tack on the selected class name if appropriate.
      selected_class = ''
      if opt_selected:
        full_classes = classes + ['selected',]
        selected_class = ' selected'
      else:
        full_classes = classes
      # Build up the class string and apply it to the item string.
      if len(full_classes) > 0:
        class_string = ' class="%s"' % ' '.join(full_classes)
      else:
        class_string = ''
      opt_string = opt_string % {'classes':class_string,}
      # Set the default parameters up.
      string_params = {'item':opt_string,
                       'sub_list': '',
                       'item_tag':item_tag,
                       'menu_level':menu_level,
                       'selected': selected_class,
                       'menu_option_id': menu_option_id,
                      }
      # If the current option is shown to have sub menus and they are allowed to
      # be displayed then recursively call this function with the option as the
      # new hierarchy index and the depth at the next level down.
      if (opt in hierarchies) and opt.show_hierarchy(opt_selected):
        sub_list = _generate_menu_string(hierarchies, opt, selected_items,
                                         selected_params, group_tag,
                                         item_tag, level=level + 1 )
        string_params['sub_list'] = sub_list
      # Add the item string to the list of sub items.
      sub_items.append(_item_template % string_params)
  # Set the default parameters for the group string up - join all the sub items
  # together into one long string.
  string_params = {'group':"\n".join(sub_items),
                   'group_tag':group_tag,
                   'menu_level':menu_level,
                  }
  return _group_template % string_params

"""
A django app for handling menus.

This app provides functionality to store a menu hierarchy in a database and use
said hierarchy to generate dynamic menus based on url of the current request.
Menus are allocated to groups and a template tag is included that allows you to
insert that menu group at the desired point of your code (in one of several
formats i.e. ul/li combinations or div/div combinations).
There are three types of menu item that may be added:
  1. Absolute Menu Items - an item that refers to a single explicit url.
  2. Named URL Menu Items - an item that refers to a named url from the a
     urls.py file.
  3. Model Menu Items - a set of items that are the result of a query. This
     must combine with a url name for generating the items.
The app integrates with django.contrib.sites if it is installed although it
should work fine without it also.
Permissions may be allocated to menu items to ensure that they are seen only
when appropriate, this includes anon,auth and staff as well as any Permission
objects that are available.

"""
__version__ = "1.0 beta"
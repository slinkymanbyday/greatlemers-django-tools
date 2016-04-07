This project is eventually going to contain a collection of several useful tools and application for use with Django.

Currently the project contains the following apps:
## Nav ##
A comprehensive menu management system that provides functionality to store a menu hierarchy in a database and use
said hierarchy to generate dynamic menus based on url of the current request.
### Features include: ###
  * Menu item grouping so that you can store different items for use on a horizontal and vertical menu.
  * Template tags allowing you to insert a menu group anywhere in your template (in one of several formats i.e. ul/li combinations, div/div combinations, or any other of your choosing).
  * Absolute menu items - an item that refers to a single explicit url.
  * Named URL menu items - an item that refers to a named url from the a urls.py file.
  * Model menu items - a set of items that are the result of a query. This combines with a url name for generating the items.
  * Integration with django.contrib.sites if it is installed (although it works fine without it).
  * The ability to restrict access to menu items to ensure that they are seen only when appropriate, this includes anon, auth and staff as well as any Permission objects that are available.

## Breadcrumbs ##
A system for generating breadcrumb trails based on where a user has visited a site.
### Features include: ###
  * A route-to-page style breadcrumb generator;
    * This shows how the user **actually** got to their current location, it _does not show_ the site hierarchy.
  * Reset points can be specified;
  * Global starting point can be specified;
  * All tracking stored in the user's session.

## Lazy Reverse ##
A simple app that allows you to use reverse named urls in places you otherwise wouldn't normally be able to.  This works by delaying the actual reverse call until the first time the string form of the url is needed.


---

All of these projects have been tested against Django 1.0.X, 1.1.X, 1.2.X and 1.3 RC 1 (from trunk `r15781`)
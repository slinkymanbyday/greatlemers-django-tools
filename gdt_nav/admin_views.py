from models import MenuOption
from forms import AbsoluteMenuOptionForm, NamedMenuOptionForm,\
                  ModelMenuOptionForm

from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404
from django.template import RequestContext
from django.shortcuts import render_to_response

from django.contrib.admin import site
from admin import *

@staff_member_required
def add_option(request, option_type):
    option_type = int(option_type)
    if option_type == MenuOption.ABSOLUTE_URL_MENU_OPTION:
        admin_class = AbsoluteMenuOptionAdmin
    elif option_type == MenuOption.NAMED_URL_MENU_OPTION:
        admin_class = NamedMenuOptionAdmin
    elif option_type == MenuOption.MODEL_MENU_OPTION:
        admin_class = ModelMenuOptionAdmin
    else:
        raise Http404
    admin_instance = admin_class(MenuOption, site)
    return admin_instance.add_view(request)
    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            form.save()
    else:
        form = form_class()
    context_dict = {'form':form}
    context = RequestContext(request, context_dict)
    return render_to_response("add_option.html", {}, context)

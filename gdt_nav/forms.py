from django.forms import ModelForm
from django import forms
from django.utils.safestring import mark_safe
from django.contrib.auth.models import Permission
from django.contrib.admin import widgets as admin_widgets
from models import MenuOption

class MenuOptionWidget(forms.HiddenInput):
    def render(self, name, value, attrs=None):
        try:
          int_val = int(value)
          hidden_input = super(MenuOptionWidget,self).render(name,int_val,attrs)
          option_type_name = dict(MenuOption.MODEL_TYPE_CHOICES)[int_val]
        except (KeyError, ValueError), e:
          hidden_input = ''
          option_type_name = 'Unknown Selection'
        return mark_safe("%s%s" % (hidden_input, option_type_name))

class MenuOptionForm(ModelForm):
    option_type = forms.ChoiceField(choices=MenuOption.MODEL_TYPE_CHOICES,
                                    widget=MenuOptionWidget)

    class Meta:
        model = MenuOption

class AbsoluteMenuOptionForm(MenuOptionForm):
    def __init__(self, *args, **kwargs):
        super(MenuOptionForm,self).__init__(*args, **kwargs)
        self.fields['option_type'].initial = MenuOption.ABSOLUTE_URL_MENU_OPTION
        self.fields['name'].help_text = """Text that should appear when the menu option is displayed."""
        self.fields['url'].required = True
        self.fields['url'].help_text = """The absolute url that represents this option."""

    class Meta(MenuOptionForm.Meta):
        exclude = ['url_name','content_type','manager','query',
                   'url_id','model_id','order_by','result_limit']

class NamedMenuOptionForm(MenuOptionForm):
    def __init__(self, *args, **kwargs):
        super(MenuOptionForm,self).__init__(*args, **kwargs)
        self.fields['option_type'].initial = MenuOption.NAMED_URL_MENU_OPTION
        self.fields['name'].help_text = """Text that should appear when the menu option is displayed."""
        self.fields['url_name'].required = True
        self.fields['url_name'].help_text = """The 'reversable' url name that represents this option."""

    class Meta(MenuOptionForm.Meta):
        exclude = ['url','content_type','manager','query',
                   'url_id','model_id','order_by','result_limit']

class ModelMenuOptionForm(MenuOptionForm):
    def __init__(self, *args, **kwargs):
        super(MenuOptionForm,self).__init__(*args, **kwargs)
        self.fields['option_type'].initial = MenuOption.MODEL_MENU_OPTION
        self.fields['name'].help_text = """A name to describe this query (will not be visible to users)."""
        self.fields['url_name'].required = True
        self.fields['url_name'].help_text = """The 'reversable' url name that represents this option."""
        self.fields['content_type'].required = True
        self.fields['content_type'].help_text = """The type of object to fetch and produce options for."""
        self.fields['manager'].required = True
        self.fields['manager'].help_text = """The object manager to use when querying the content_type."""
        self.fields['query'].help_text = """The query to use to filter down the content_type objects- format is as if entering directly into a django filter, comma separate multiple restrictions."""
        self.fields['url_id'].required = True
        self.fields['url_id'].help_text = """The id in the named url that this query provides."""
        self.fields['model_id'].required = True
        self.fields['model_id'].help_text = """The local attribute to map to the url_id above."""
        #self.fields['order_by'].required = True
        self.fields['order_by'].help_text = """Any sorting to be done on the query - format is as if entering directly into a django order_by filter, comma separate multiple order keys - will happen after filtering."""
        #self.fields['result_limit'].required = True
        self.fields['result_limit'].help_text = """Number of results to return."""

    class Meta(MenuOptionForm.Meta):
        exclude = ['url']

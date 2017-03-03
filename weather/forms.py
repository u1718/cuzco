from django.forms import ModelForm
from weather.models import City
from django.utils.translation import ugettext_lazy as _

class CityModelForm(ModelForm):
    class Meta:
        model = City
        fields = ('name', 'ds_owm', 'ds_yahoo')
        labels = {
            'name': _('City'),
            'ds_owm': _('Data source(OWM)'),
            'ds_yahoo': _('Data source(Yahoo)'),
        }

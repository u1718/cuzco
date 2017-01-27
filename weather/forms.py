from django.forms import ModelForm
from weather.models import City

class CityModelForm(ModelForm):
    class Meta:
        model = City
        fields = ['name', 'ds_owm']

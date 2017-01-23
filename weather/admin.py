from django.contrib import admin

# Register your models here.

from .models import City, OWM, OWMForecast

class OWMAdmin(admin.ModelAdmin):
    model = OWM
    #list_display = ('wine', 'rating', 'user_name', 'comment', 'pub_date')
    list_filter = ['req_date', 'name', 'city']
    #search_fields = ['comment']

class OWMForecastAdmin(admin.ModelAdmin):
    model = OWMForecast
    #list_display = ('wine', 'rating', 'user_name', 'comment', 'pub_date')
    #list_filter = ['owm']
    search_fields = ['forecast_text']

admin.site.register(City)
admin.site.register(OWM, OWMAdmin)
admin.site.register(OWMForecast, OWMForecastAdmin)

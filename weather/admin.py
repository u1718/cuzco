from django.contrib import admin

# Register your models here.

from .models import City, OWM, OWMForecast, Yahoo, YahooForecast

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

class YahooAdmin(admin.ModelAdmin):
    model = Yahoo
    #list_display = ('wine', 'rating', 'user_name', 'comment', 'pub_date')
    list_filter = ['req_date', 'name', 'city']
    #search_fields = ['comment']

class YahooForecastAdmin(admin.ModelAdmin):
    model = YahooForecast
    #list_display = ('wine', 'rating', 'user_name', 'comment', 'pub_date')
    #list_filter = ['owm']
    search_fields = ['forecast_text']

admin.site.register(City)
admin.site.register(OWM, OWMAdmin)
admin.site.register(OWMForecast, OWMForecastAdmin)
admin.site.register(Yahoo, YahooAdmin)
admin.site.register(YahooForecast, YahooForecastAdmin)

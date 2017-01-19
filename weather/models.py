from django.db import models

# Create your models here.
import datetime
from django.utils import timezone

class City(models.Model):
    name = models.CharField(max_length=100)
    ds_owm = models.URLField()

    def __str__(self):
        return self.name

class OWM(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    req_date = models.DateTimeField('request date')
    iden = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    coord_lon = models.CharField(max_length=100)
    coord_lat = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    population = models.CharField(max_length=100)
    sys_population = models.CharField(max_length=100)
    cod = models.CharField(max_length=100)
    message = models.CharField(max_length=100)
    cnt = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    def was_requested_recently(self):
        return self.req_date >= timezone.now() - datetime.timedelta(days=1)

class OWMForecast(models.Model):
    owm = models.ForeignKey(OWM, on_delete=models.CASCADE)
    forecast_text = models.CharField(max_length=1200)

    def __str__(self):
        return self.forecast_text


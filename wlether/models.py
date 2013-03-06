from django.db import models

# Create your models here.

class Scan(models.Model):
    chassis = models.CharField(max_length=200)
    adapter = models.CharField(max_length=200)
    tool = models.CharField(max_length=200)
    scan_time = models.DateTimeField('time scaned')
    def __unicode__(self):
        return self.scan_time


class APoint (models.Model):                       #
    scan = models.ForeignKey(Scan)
    bssid = models.CharField(max_length=50)        #bssid VARCHAR(50),
    frequency = models.CharField(max_length=50)    #frequency VARCHAR(50),
    signal_level = models.CharField(max_length=50) #signal_level VARCHAR(50),
    flags = models.CharField(max_length=50)        #flags VARCHAR(50),
    ssid = models.CharField(max_length=50)         #ssid VARCHAR(50),
    def __unicode__(self):
        return self.ssid

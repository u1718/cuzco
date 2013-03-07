from django.db import models

# Create your models here.

class Scan(models.Model):
    chassis = models.CharField(max_length=200)
    adapter = models.CharField(max_length=200)
    tool = models.CharField(max_length=200)
    scan_time = models.DateTimeField('time scaned')

    def __unicode__(self):
        return unicode(self.scan_time)


class APoint (models.Model):
    scan = models.ForeignKey(Scan)
    bssid = models.CharField(max_length=50)
    frequency = models.CharField(max_length=50)
    signal_level = models.CharField(max_length=50)
    flags = models.CharField(max_length=50)
    ssid = models.CharField(max_length=50)

    def was_it_channel_6(self):
        return self.frequency == '2437'

    was_it_channel_6.admin_order_field = 'frequency'
    was_it_channel_6.boolean = True
    was_it_channel_6.short_description = 'Channel 6?'

    def __unicode__(self):
        return self.ssid

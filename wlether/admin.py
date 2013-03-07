from django.contrib import admin
from wlether.models import Scan, APoint

# class ScanAdmin(admin.ModelAdmin):
#     #fields = ['scan_time', 'chassis', 'adapter', 'tool']
#     fieldsets = [
#         (None,               {'fields': ['chassis', 'adapter', 'tool']}),
#         ('Date information', {'fields': ['scan_time']}),
#         ]

# admin.site.register(Scan, ScanAdmin)

# admin.site.register(APoint)

class APointAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['scan', 'bssid', 'frequency', 'signal_level', 'flags', 'ssid']}),
        ]
    list_display = ('scan', 'bssid', 'frequency', 'signal_level', 'flags', 'ssid', 'was_it_channel_6')
    list_filter = ['frequency']
    search_fields = ['ssid']

admin.site.register(APoint, APointAdmin)

class APontInline(admin.TabularInline): # admin.StackedInline
    model = APoint
    extra = 1
    fieldsets = [
        (None,               {'fields': ['bssid', 'frequency', 'signal_level', 'flags', 'ssid']}),
        ]
    # TODO(m): find out appropriate Inline methods
    #list_display = ('bssid', 'frequency', 'signal_level', 'flags', 'ssid', 'was_it_channel_6')
    #list_filter = ['frequency']
    #search_fields = ['ssid']

class ScanAdmin(admin.ModelAdmin):
     fieldsets = [
         (None,               {'fields': ['chassis', 'adapter', 'tool']}),
         ('Time information', {'fields': ['scan_time'], 'classes': ['collapse']}),
         ]
     inlines = [APontInline]
     list_display = ('scan_time', 'chassis', 'adapter', 'tool')
     list_filter = ['scan_time']
     date_hierarchy = 'scan_time'

admin.site.register(Scan, ScanAdmin)

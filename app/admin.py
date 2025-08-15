from django.contrib import admin
from .models import UserTracker, DeviceTracker

class UserTrackerAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'total_devices', 'total_co2', 'total_kwh']
    search_fields = ['user_id__username']

class DeviceTrackerAdmin(admin.ModelAdmin):
    list_display = ['device_name', 'user', 'device_co2', 'device_kwh']
    search_fields = ['device_name', 'user__username']

admin.site.register(UserTracker, UserTrackerAdmin)
admin.site.register(DeviceTracker, DeviceTrackerAdmin)
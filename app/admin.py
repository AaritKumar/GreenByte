from django.contrib import admin
from .models import UserTracker

class UserTrackerAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'total_devices', 'total_co2', 'total_kwh']
    search_fields = ['user_id__username']

admin.site.register(UserTracker, UserTrackerAdmin)
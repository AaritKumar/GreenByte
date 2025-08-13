from django.db import models
from django.contrib.auth.models import User

class UserTracker(models.Model):
    user_id = models.OneToOneField(User, on_delete=models.CASCADE)
    total_devices = models.IntegerField(default=0)
    total_co2 = models.IntegerField(default=0)
    total_kwh = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Tracker for {self.user_id.username}"
    
    class Meta:
        verbose_name = "User Tracker"
        verbose_name_plural = "User Trackers"

class DeviceTracker(models.Model):
    device_name = models.CharField(max_length=255)
    device_co2 = models.IntegerField(default=0)
    device_kwh = models.IntegerField(default=0)

    def __str__(self):
        return self.device_name
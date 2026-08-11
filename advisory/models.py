from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class District(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    province = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class Crop(models.Model):
    name = models.CharField(max_length=100)
    season = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    def __str__(self):
        return self.name

class FarmerProfile(models.Model):
    SOIL_CHOICES = [
        ('clay', 'Clay'),
        ('sandy', 'Sandy'),
        ('loam', 'Loam'),
        ('mixed', 'Mixed'),
        ('silt', 'Silt'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    farmer_id = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=15, unique=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True)
    village = models.CharField(max_length=100, blank=True)
    field_area = models.FloatField(help_text="Area in Ropani")
    soil_type = models.CharField(max_length=20, choices=SOIL_CHOICES)
    primary_crop = models.ForeignKey(Crop, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.farmer_id} - {self.user.get_full_name()}"

    def get_initials(self):
        name = self.user.get_full_name()
        parts = name.strip().split()
        if len(parts) >= 2:
            return parts[0][0].upper() + parts[1][0].upper()
        elif parts:
            return parts[0][0].upper()
        return "F"

class CropRule(models.Model):
    SEVERITY = [
        ('suitable', 'Suitable'),
        ('warning', 'Warning'),
        ('unsuitable', 'Unsuitable'),
    ]
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    parameter = models.CharField(max_length=50)
    condition = models.CharField(max_length=50)
    min_value = models.FloatField(null=True, blank=True)
    max_value = models.FloatField(null=True, blank=True)
    action = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY)
    source = models.CharField(max_length=200, blank=True)
    def __str__(self):
        return f"{self.crop.name} - {self.parameter} - {self.severity}"

class WeatherData(models.Model):
    district = models.ForeignKey(District, on_delete=models.CASCADE)
    temperature = models.FloatField()
    humidity = models.FloatField()
    rainfall = models.FloatField()
    wind_speed = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

class Advisory(models.Model):
    district = models.ForeignKey(District, on_delete=models.CASCADE)
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    weather = models.ForeignKey(WeatherData, on_delete=models.CASCADE, null=True)
    suitability = models.CharField(max_length=20)
    risk_level = models.CharField(max_length=20, blank=True)
    recommendation = models.JSONField()
    generated_at = models.DateTimeField(auto_now_add=True)
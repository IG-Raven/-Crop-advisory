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
    season = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class CropRule(models.Model):
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    parameter = models.CharField(max_length=50)
    min_value = models.FloatField(null=True, blank=True)
    max_value = models.FloatField(null=True, blank=True)
    action = models.TextField()
    severity = models.CharField(max_length=50, choices=[('low', 'Low'), ('moderate', 'Moderate'), ('high', 'High')])
    condition = models.CharField(max_length=20)
    source = models.CharField(max_length=200, blank=True)
    def __str__(self):
        return f"{self.crop.name} - {self.district.name}"
    
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
    weather = models.ForeignKey(WeatherData, on_delete=models.CASCADE)
    suitability = models.CharField(max_length=20)
    recommendation = models.JSONField()
    generated_at = models.DateTimeField(auto_now_add=True)
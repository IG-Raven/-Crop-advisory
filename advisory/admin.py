from django.contrib import admin
from .models import District, Crop, CropRule, WeatherData, Advisory
# Register your models here.

admin.site.register(District)
admin.site.register(Crop)
admin.site.register(CropRule)
admin.site.register(WeatherData)
admin.site.register(Advisory) 
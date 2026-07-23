from django.core.management.base import BaseCommand
from advisory.models import District, Crop, CropRule

class Command(BaseCommand):
     def handle(self, *args, **kwargs):
        districts = [
            ("Chitwan", 27.52, 84.35, "Bagmati"),
            ("Bardiya", 28.30, 81.45, "Lumbini"),
            ("Rupandehi", 27.63, 83.45, "Lumbini"),
            ("Sunsari", 26.63, 87.17, "Koshi"),
        ]
        for name, lat, lon, prov in districts:
            District.objects.get_or_create(name=name, latitude=lat, longitude=lon, province=prov)

        crops = ["Rice", "Wheat", "Maize", "Vegetables"]
        for c in crops:
            Crop.objects.get_or_create(name=c)

        rice = Crop.objects.get(name="Rice")
        wheat = Crop.objects.get(name="Wheat")
        maize = Crop.objects.get(name="Maize")
        veg = Crop.objects.get(name="Vegetables")
        
        rules = [
            # 2 rules for Rice
            (rice, "temperature", 20, 35, "Suitable for planting", "suitable"),
            (rice, "temperature", 35, 40, "Monitor closely, heat stress risk", "warning"),
            (rice, "temperature", 40, None, "Unsuitable, delay planting", "unsuitable"),
            (rice, "rainfall", 0, 5, "Irrigate now, rainfall too low", "unsuitable"),
            (rice, "rainfall", 50, None, "Delay fertiliser, heavy rainfall risk", "warning"),
            
            # 2 rules for Wheat
            (wheat, "temperature", 10, 25, "Suitable for planting", "suitable"),
            (wheat, "temperature", 30, None, "Unsuitable, too hot for wheat", "unsuitable"),
            
            # 2 rules for Maize 
            (maize, "temperature", 18, 32, "Suitable for planting", "suitable"),
            (maize, "temperature", 38, None, "Unsuitable, extreme heat", "unsuitable"),
            
            # 2 rules for Vegetables 
            (veg, "temperature", 15, 30, "Suitable for planting", "suitable"),
            (veg, "temperature", 35, None, "Unsuitable, too hot for vegetables", "unsuitable"),
        ]
        for crop, param, mn, mx, action, sev in rules:
            CropRule.objects.get_or_create(crop=crop, parameter=param, min_value=mn, max_value=mx, action=action, severity=sev)

        self.stdout.write("Seed complete")
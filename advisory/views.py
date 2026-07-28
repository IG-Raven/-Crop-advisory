from django.http import HttpResponse
from django.shortcuts import render
from django.core.cache import cache
from .models import District, Crop, CropRule, WeatherData, Advisory
from .weather_utils import fetch_weather
from .advisory_engine import get_advisory
# Create your views here.

def home(request):
    districts = District.objects.all()
    crops = Crop.objects.all()
    return render(request, "advisory/home.html", {"districts": District.objects.all(), "crops": Crop.objects.all()})


def results(request):
    if request.method == "POST":
        district_name = request.POST.get("district")
        crop_name = request.POST.get("crop")

        try:
            district = District.objects.get(name=district_name)
            crop = Crop.objects.get(name=crop_name)
            weather = fetch_weather(district.latitude, district.longitude)
            advisory = get_advisory(crop_name, weather)

            return render(request, "advisory/results.html", {
                "district": district,
                "crop": crop,
                "weather": weather,
                "advisory": advisory,
            })

        except Exception as e:
            return render(request, "advisory/home.html", {
                "districts": District.objects.all(),
                "crops": Crop.objects.all(),
                "error": str(e),
            })

    return render(request, "advisory/home.html", {
        "districts": District.objects.all(),
        "crops": Crop.objects.all(),
    })
    
def login_view(request):
    return render(request, "advisory/login.html")

def register_view(request):
    return render(request, "advisory/register.html")

def dashboard_view(request):
    return HttpResponse("Dashboard coming soon.")

def about_view(request):
    return HttpResponse("About page coming soon.")
    
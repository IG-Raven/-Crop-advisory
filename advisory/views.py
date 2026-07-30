import os
import json
import anthropic
from django.http import JsonResponse
from django.http import HttpResponse
from django.shortcuts import render, redirect
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
    if request.method == "POST":
        request.session['logged_in'] = True
        return redirect("/dashboard/")
    return render(request, "advisory/login.html")

def dashboard_view(request):
    if not request.session.get('logged_in'):
        return redirect("/login/")
    return render(request, "advisory/dashboard.html", {
        "farmer_name": "Ram Bahadur",
        "farmer_name_ne": "राम बहादुर",
        "district": "Chitwan",
        "ward": "4",
        "crop": "Rice (Dhan)",
        "temp": "32°C, Sunny",
        "humidity": "45%",
    })

def logout_view(request):
    request.session.flush()
    return redirect("/")

def weather_data_view(request):
    return render(request, "advisory/weather_data.html")

def register_view(request):
    return render(request, "advisory/register.html")

def about_view(request):
    return render(request, "advisory/about.html")

def chatbot_view(request):
    return render(request, "advisory/chatbot.html")

def chatbot_message(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "")
            history = data.get("history", [])

            client = anthropic.Anthropic(
                api_key=os.environ.get("ANTHROPIC_API_KEY")
            )

            system_prompt = """You are an expert agricultural advisor for Nepal's Terai region farmers.
You specialize in Rice (Dhaan), Wheat (Gahu), Maize (Makai), and Vegetables.
You focus on Chitwan, Bardiya, Rupandehi, and Sunsari districts.
Give practical, concise, actionable advice based on MoALD Nepal guidelines and FAO standards.
Use simple language. Mention specific quantities when relevant.
You can respond in Nepali if the farmer writes in Nepali.
Always end with one clear actionable next step."""

            messages = []
            for h in history[:-1]:
                if h.get("role") in ("user", "assistant"):
                    messages.append({"role": h["role"], "content": h["content"]})

            messages.append({"role": "user", "content": user_message})

            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=500,
                system=system_prompt,
                messages=messages
            )

            reply = response.content[0].text
            return JsonResponse({"reply": reply})

        except Exception as e:
            return JsonResponse({"reply": f"Error: {str(e)}"}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)

api_key = os.environ.get("ANTHROPIC_API_KEY")
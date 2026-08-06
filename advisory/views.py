import sys
import os
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.core.cache import cache
from .models import District, Crop, CropRule, WeatherData, Advisory
from .weather_utils import fetch_weather
from .advisory_engine import get_advisory
from bert_bot.advisor import AgricultureAdvisor


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from bert_bot.advisor import AgricultureAdvisor

# Load BERT RAG model once when server starts
ADVISOR = AgricultureAdvisor(
    data_path=os.path.join(BASE_DIR, 'bert_bot', 'agriculture_data.json')
)

def home(request):
    return render(request, "advisory/home.html", {
        "districts": District.objects.all(),
        "crops": Crop.objects.all()
    })

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

def chatbot_message(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_message = data.get("message", "")

        result = ADVISOR.ask(user_message)

        # Save to session history
        history = request.session.get("chat_history", [])
        history.append({
            "question": user_message,
            "answer": result["answer"],
            "confidence": result["confidence"]
        })
        request.session["chat_history"] = history[-20:]
        request.session.modified = True

        return JsonResponse({"reply": result["answer"]})

    return JsonResponse({"error": "Method not allowed"}, status=405)

def chatbot_history(request):
    history = request.session.get("chat_history", [])
    return JsonResponse({"history": history})